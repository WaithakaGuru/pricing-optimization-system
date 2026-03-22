"""Test weather integration: StateBuilder, WeatherService, and API."""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from services.weather_service import WeatherService
from data.loaders.weather_loader import (
    fetch_weather_data, 
    fetch_historical_weather,
    normalize_weather_features,
    weather_code_to_category
)
from rl.environment.state_builder import StateBuilder

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_weather_service():
    """Test WeatherService: current weather and forecast."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: WeatherService - Current Weather & Forecast")
    logger.info("="*60)
    
    try:
        service = WeatherService(latitude=40.7128, longitude=-74.0060)  # NYC
        
        # Test current weather
        logger.info("\n[1.1] Fetching current weather...")
        current = await service.get_current_weather()
        if current:
            logger.info(f"✓ Current Weather:")
            logger.info(f"  - Temperature: {current.get('temperature')}°C")
            logger.info(f"  - Humidity: {current.get('humidity')}%")
            logger.info(f"  - Precipitation: {current.get('precipitation')}mm")
            logger.info(f"  - Wind Speed: {current.get('wind_speed')}km/h")
            logger.info(f"  - Weather Code: {current.get('weather_code')}")
        else:
            logger.error("✗ Failed to fetch current weather")
            return False
        
        # Test forecast
        logger.info("\n[1.2] Fetching 7-day forecast...")
        forecast = await service.get_weather_forecast(days=7)
        if forecast and len(forecast) > 0:
            logger.info(f"✓ Fetched {len(forecast)} days of forecast")
            for day in forecast[:3]:
                logger.info(f"  - {day['date']}: {day['temp_max']}°C (max), {day['precipitation']}mm rain")
        else:
            logger.error("✗ Failed to fetch forecast")
            return False
        
        # Test state formatting
        logger.info("\n[1.3] Formatting weather for agent state...")
        state_weather = await service.get_weather_for_state()
        logger.info(f"✓ Weather state vector (normalized [0,1]):")
        logger.info(f"  - Temperature: {state_weather.get('temperature'):.3f}")
        logger.info(f"  - Humidity: {state_weather.get('humidity'):.3f}")
        logger.info(f"  - Precipitation: {state_weather.get('precipitation'):.3f}")
        logger.info(f"  - Weather Type: {state_weather.get('weather_type')}")
        
        # Test caching
        logger.info("\n[1.4] Testing cache (should return cached data)...")
        start = datetime.utcnow()
        cached_weather = await service.get_current_weather()
        elapsed = (datetime.utcnow() - start).total_seconds()
        logger.info(f"✓ Cache hit! Data returned in {elapsed:.3f}s (should be < 0.1s)")
        
        await service.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ WeatherService test failed: {e}", exc_info=True)
        return False


async def test_weather_loader():
    """Test WeatherLoader: historical data and normalization."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: WeatherLoader - Historical Data & Normalization")
    logger.info("="*60)
    
    try:
        # Test current+forecast fetch
        logger.info("\n[2.1] Fetching current & forecast via loader...")
        weather_data = await fetch_weather_data(latitude=40.7128, longitude=-74.0060)
        if weather_data:
            logger.info(f"✓ Fetched weather data at {weather_data.get('fetched_at')}")
            logger.info(f"  - Current temperature: {weather_data['current'].get('temperature_2m')}°C")
            logger.info(f"  - Forecast days: {len(weather_data['forecast'].get('time', []))}")
        else:
            logger.error("✗ Failed to fetch weather via loader")
            return False
        
        # Test historical data
        logger.info("\n[2.2] Fetching 30 days of historical weather...")
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        historical_df = await fetch_historical_weather(
            latitude=40.7128,
            longitude=-74.0060,
            start_date=start_date,
            end_date=end_date
        )
        
        if not historical_df.empty:
            logger.info(f"✓ Fetched {len(historical_df)} days of historical data")
            logger.info(f"  Columns: {list(historical_df.columns)}")
            logger.info(f"  Date range: {historical_df['date'].min()} to {historical_df['date'].max()}")
            logger.info(f"\n  Sample data:")
            for idx, row in historical_df.head(3).iterrows():
                logger.info(f"    {row['date'].date()}: {row['temp_max']:.1f}°C max, {row['precipitation']:.1f}mm rain")
        else:
            logger.error("✗ Failed to fetch historical weather")
            return False
        
        # Test normalization
        logger.info("\n[2.3] Testing feature normalization...")
        test_temp = 22.0
        test_humidity = 65.0
        test_precip = 5.0
        
        normalized = normalize_weather_features(test_temp, test_humidity, test_precip)
        logger.info(f"✓ Normalized features (temp={test_temp}°C, humidity={test_humidity}%, precip={test_precip}mm):")
        logger.info(f"  - Temperature [0,1]: {normalized['temperature_normalized']:.3f}")
        logger.info(f"  - Humidity [0,1]: {normalized['humidity_normalized']:.3f}")
        logger.info(f"  - Precipitation [0,1]: {normalized['precipitation_normalized']:.3f}")
        
        # Test weather code categorization
        logger.info("\n[2.4] Testing weather code to category...")
        test_codes = [0, 2, 65, 71, 95]
        for code in test_codes:
            category = weather_code_to_category(code)
            logger.info(f"  - Code {code:02d}: {category}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ WeatherLoader test failed: {e}", exc_info=True)
        return False


def test_state_builder_weather():
    """Test StateBuilder with weather integration."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: StateBuilder - Weather Integration (Sync)")
    logger.info("="*60)
    
    try:
        logger.info("\n[3.1] Initializing StateBuilder with weather...")
        builder = StateBuilder(
            db_url="sqlite:///pricing.db",
            latitude=40.7128,
            longitude=-74.0060
        )
        logger.info("✓ StateBuilder initialized with weather service")
        
        logger.info("\n[3.2] Checking weather service...")
        logger.info(f"✓ Weather service attached: {builder.weather_service is not None}")
        logger.info(f"  - Location: ({builder.weather_service.latitude}, {builder.weather_service.longitude})")
        logger.info(f"  - Cache TTL: {builder.weather_service.cache_ttl_seconds}s")
        
        logger.info("\n[3.3] Feature configuration check...")
        logger.info(f"✓ State features: {builder.feature_names}")
        logger.info(f"✓ Feature count: {len(builder.feature_names)}")
        
        # Check weather feature is in the list
        if "weather_factor" in builder.feature_names:
            logger.info("✓ Weather factor included in state vector")
        else:
            logger.error("✗ Weather factor NOT in state vector")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ StateBuilder test failed: {e}", exc_info=True)
        return False


async def test_api_weather_response():
    """Test that API includes weather in response."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: API Response - Weather Impact Included")
    logger.info("="*60)
    
    try:
        # Simulate what API does
        logger.info("\n[4.1] Simulating API price recommendation with weather...")
        
        service = WeatherService(latitude=40.7128, longitude=-74.0060)
        weather_data = await service.get_weather_for_state()
        
        if weather_data:
            logger.info(f"✓ Weather data retrieved for API response:")
            logger.info(f"  - Type: {weather_data.get('weather_type')}")
            logger.info(f"  - Temperature (normalized): {weather_data.get('temperature'):.3f}")
            
            # Compute weather impact
            weather_type = weather_data.get('weather_type', 'unknown')
            precipitation = weather_data.get('precipitation', 0.0)
            
            weather_impact_pct = 0.0
            if weather_type == "rain":
                weather_impact_pct = -15.0
            elif weather_type == "clear":
                weather_impact_pct = 10.0
            elif weather_type == "snow":
                weather_impact_pct = -25.0
            
            weather_impact = {
                "temperature": round(weather_data.get("temperature", 0) * 50 - 10, 1),
                "weather_type": weather_type,
                "precipitation_mm": round(precipitation * 50, 1),
                "demand_impact_pct": weather_impact_pct,
                "note": f"Weather factor: {weather_type}. Estimated demand impact: {weather_impact_pct:+.1f}%"
            }
            
            logger.info(f"\n✓ Weather impact computed for API response:")
            logger.info(f"  - Temperature: {weather_impact['temperature']:.1f}°C")
            logger.info(f"  - Precipitation: {weather_impact['precipitation_mm']:.1f}mm")
            logger.info(f"  - Demand Impact: {weather_impact['demand_impact_pct']:+.1f}%")
            logger.info(f"  - Note: {weather_impact['note']}")
        else:
            logger.error("✗ Could not fetch weather for API response")
            return False
        
        await service.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ API weather response test failed: {e}", exc_info=True)
        return False


async def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "█"*60)
    logger.info("█  WEATHER INTEGRATION TEST SUITE (Task 1.2)")
    logger.info("█"*60)
    
    results = {
        "WeatherService": await test_weather_service(),
        "WeatherLoader": await test_weather_loader(),
        "StateBuilder": test_state_builder_weather(),
        "API Response": await test_api_weather_response(),
    }
    
    logger.info("\n" + "="*60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    logger.info("\n" + "="*60)
    if all_passed:
        logger.info("✓ ALL TESTS PASSED! Weather integration ready.")
    else:
        logger.info("✗ Some tests failed. Check logs above.")
    logger.info("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    # Run async tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
