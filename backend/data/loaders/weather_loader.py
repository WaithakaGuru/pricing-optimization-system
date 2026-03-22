"""Load weather data from Open-Meteo API."""
import logging
import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"


async def fetch_weather_data(latitude: float, longitude: float) -> dict:
    """
    Fetch current and forecast weather from Open-Meteo (free API).
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        
    Returns:
        Weather data dict with current and forecast keys
    """
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            # Fetch current weather (use /forecast endpoint with current parameter)
            current_url = "https://api.open-meteo.com/v1/forecast"
            current_params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            }
            
            current_response = await client.get(current_url, params=current_params)
            current_response.raise_for_status()
            current_data = current_response.json()["current"]
            
            # Fetch forecast
            forecast_url = "https://api.open-meteo.com/v1/forecast"
            forecast_params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
                "forecast_days": 7,
            }
            
            forecast_response = await client.get(forecast_url, params=forecast_params)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()["daily"]
            
            logger.info(f"Fetched weather data for ({latitude}, {longitude})")
            return {
                "current": current_data,
                "forecast": forecast_data,
                "fetched_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {e}")
            raise


async def fetch_historical_weather(
    latitude: float,
    longitude: float,
    start_date: datetime,
    end_date: datetime,
    temperature_unit: str = "celsius",
) -> pd.DataFrame:
    """
    Fetch historical weather data from Open-Meteo archive.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        temperature_unit: Temperature unit (celsius or fahrenheit)
        
    Returns:
        DataFrame with historical weather data
        Columns: date, temp_max, temp_min, temp_mean, precipitation, weather_code
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            url = BASE_URL
            
            # Format dates as YYYY-MM-DD
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_str,
                "end_date": end_str,
                "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,weather_code",
                "temperature_unit": temperature_unit,
                "timezone": "UTC",
            }
            
            logger.info(f"Fetching historical weather from {start_str} to {end_str}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json().get("daily", {})
            
            if not data or not data.get("time"):
                logger.warning("No historical weather data returned")
                return pd.DataFrame()
            
            # Construct DataFrame
            df = pd.DataFrame({
                "date": pd.to_datetime(data["time"]),
                "temp_max": data.get("temperature_2m_max", []),
                "temp_min": data.get("temperature_2m_min", []),
                "temp_mean": data.get("temperature_2m_mean", []),
                "precipitation": data.get("precipitation_sum", []),
                "weather_code": data.get("weather_code", []),
            })
            
            logger.info(f"Fetched {len(df)} days of historical weather data")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch historical weather: {e}")
            raise


def normalize_weather_features(
    temperature: float,
    humidity: float,
    precipitation: float,
    min_temp: float = -10,
    max_temp: float = 40,
) -> dict:
    """
    Normalize weather features to [0, 1] range for ML models.
    
    Args:
        temperature: Temperature in Celsius
        humidity: Relative humidity (0-100)
        precipitation: Precipitation in mm
        min_temp: Minimum expected temperature for normalization
        max_temp: Maximum expected temperature for normalization
        
    Returns:
        Dict with normalized features
    """
    # Temperature: [-10, 40] → [0, 1]
    temp_norm = max(0.0, min(1.0, (temperature - min_temp) / (max_temp - min_temp)))
    
    # Humidity: [0, 100] → [0, 1]
    humidity_norm = humidity / 100.0
    
    # Precipitation: [0, 50mm] → [0, 1]
    precip_norm = min(1.0, precipitation / 50.0)
    
    return {
        "temperature_normalized": temp_norm,
        "humidity_normalized": humidity_norm,
        "precipitation_normalized": precip_norm,
    }


def weather_code_to_category(code: int) -> str:
    """
    Convert WMO weather code to category.
    
    Args:
        code: WMO weather code
        
    Returns:
        Weather category (clear, cloudy, rain, snow, etc.)
    """
    if code in [0, 1]:
        return "clear"
    elif code in [2, 3]:
        return "cloudy"
    elif code in [45, 48]:
        return "foggy"
    elif code in [51, 53, 55]:
        return "drizzle"
    elif code in [61, 63, 65, 80, 81, 82]:
        return "rain"
    elif code in [71, 73, 75, 85, 86]:
        return "snow"
    elif code == 95:
        return "thunderstorm"
    else:
        return "unknown"
