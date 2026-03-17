"""Load weather data from Open-Meteo API."""
import logging
import httpx
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


async def fetch_weather_data(latitude: float, longitude: float) -> dict:
    """
    Fetch current and forecast weather from Open-Meteo (free API).
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        
    Returns:
        Weather data dict
    """
    # TODO: Call Open-Meteo API
    # TODO: Parse and return current weather + forecast
    pass


async def fetch_historical_weather(
    latitude: float, longitude: float, start_date: datetime, end_date: datetime
) -> pd.DataFrame:
    """Fetch historical weather data."""
    # TODO: Fetch from Open-Meteo archive endpoint
    return pd.DataFrame()
