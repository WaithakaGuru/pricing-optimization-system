"""Weather service - real external weather data integration."""
import logging
import httpx
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service for fetching real weather data from Open-Meteo API (free, no auth needed).
    
    Weather data feeds the RL agent's state space for:
    - Seasonal demand patterns (cold → heating products, hot → cooling)
    - Weather-dependent elasticity (rain → umbrellas, snow → boots)
    - Real-time decision context
    
    Open-Meteo API: https://open-meteo.com/ (free tier, generous limits)
    """

    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1",
        latitude: float = 40.7128,  # Default: NYC
        longitude: float = -74.0060,
        timeout: int = 10,
    ):
        """
        Initialize weather service.
        
        Args:
            base_url: Open-Meteo API base URL
            latitude: Location latitude (default NYC)
            longitude: Location longitude (default NYC)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.latitude = latitude
        self.longitude = longitude
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(
            f"WeatherService initialized for location ({latitude}, {longitude})"
        )

    async def get_current_weather(self) -> Optional[Dict]:
        """
        Fetch current weather from Open-Meteo.
        
        Returns:
            Dict with temperature, humidity, precipitation, etc.
            Example:
            {
                "temperature": 22.5,
                "humidity": 65,
                "precipitation": 0.0,
                "weather_code": 80,  # Light rain
                "wind_speed": 12.5,
                "timestamp": "2024-03-19T10:00:00Z"
            }
        """
        try:
            url = f"{self.base_url}/current"
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            current = data.get("current", {})
            
            weather_dict = {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation", 0),
                "weather_code": current.get("weather_code"),
                "wind_speed": current.get("wind_speed_10m"),
                "time": current.get("time"),
                "timezone": data.get("timezone"),
            }
            
            logger.info(f"Current weather: {weather_dict['temperature']}°C, {weather_dict['weather_code']}")
            return weather_dict
            
        except Exception as e:
            logger.error(f"Failed to fetch current weather: {e}")
            return None

    async def get_weather_forecast(self, days: int = 7) -> Optional[List[Dict]]:
        """
        Fetch weather forecast from Open-Meteo.
        
        Args:
            days: Number of days to forecast (1-16)
            
        Returns:
            List of daily forecasts
            Example: [
                {
                    "date": "2024-03-19",
                    "temp_max": 25.0,
                    "temp_min": 15.0,
                    "precipitation": 0.5,
                    "weather_code": 80,
                },
                ...
            ]
        """
        try:
            days = min(max(days, 1), 16)  # Clamp to 1-16
            
            url = f"{self.base_url}/forecast"
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
                "forecast_days": days,
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            daily = data.get("daily", {})
            
            dates = daily.get("time", [])
            temps_max = daily.get("temperature_2m_max", [])
            temps_min = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            codes = daily.get("weather_code", [])
            
            forecast = [
                {
                    "date": d,
                    "temp_max": t_max,
                    "temp_min": t_min,
                    "precipitation": p,
                    "weather_code": c,
                }
                for d, t_max, t_min, p, c in zip(dates, temps_max, temps_min, precip, codes)
            ]
            
            logger.info(f"Forecast fetched: {len(forecast)} days")
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to fetch weather forecast: {e}")
            return None

    def interpret_weather_code(self, code: int) -> str:
        """
        Interpret WMO weather code.
        
        Args:
            code: WMO weather code
            
        Returns:
            Human-readable description
        """
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
        }
        return codes.get(code, f"Unknown ({code})")

    async def get_weather_for_state(self) -> Dict:
        """
        Get weather data formatted for RL agent state space.
        
        Returns:
            Dict with normalized weather features for state builder
            {
                "temperature": 22.5,  # Celsius, normalized to [0, 1]
                "humidity": 0.65,     # [0, 1]
                "precipitation": 0.0, # [0, 1]
                "weather_type": "rain" # categorical
            }
        """
        weather = await self.get_current_weather()
        
        if not weather:
            logger.warning("Using default weather due to fetch failure")
            return {
                "temperature": 20.0,
                "humidity": 0.5,
                "precipitation": 0.0,
                "weather_type": "clear",
            }
        
        # Normalize temperature: [-10, 40] → [0, 1]
        temp_norm = min(max((weather["temperature"] + 10) / 50, 0), 1)
        
        # Humidity already [0, 100]
        humidity_norm = weather["humidity"] / 100.0
        
        # Precipitation: [0, 50mm] → [0, 1]
        precip_norm = min(weather["precipitation"] / 50, 1.0)
        
        # Weather type
        weather_code = weather["weather_code"]
        if weather_code in [0, 1]:
            weather_type = "clear"
        elif weather_code in [2, 3]:
            weather_type = "cloudy"
        elif weather_code in [45, 48]:
            weather_type = "foggy"
        elif weather_code in [61, 63, 65, 80, 81, 82]:
            weather_type = "rain"
        elif weather_code in [71, 73, 75, 85, 86]:
            weather_type = "snow"
        elif weather_code == 95:
            weather_type = "storm"
        else:
            weather_type = "drizzle"
        
        return {
            "temperature": temp_norm,
            "humidity": humidity_norm,
            "precipitation": precip_norm,
            "weather_type": weather_type,
        }

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
