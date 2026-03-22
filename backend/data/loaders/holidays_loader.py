"""Load holiday calendar and compute seasonality adjustments."""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def get_holidays_for_year(year: int, country: str = "US") -> Dict[datetime, str]:
    """
    Get holidays for a given year using the holidays library.
    
    Args:
        year: Year to fetch holidays for
        country: Country code (default: US)
        
    Returns:
        Dict mapping date -> holiday name
    """
    try:
        import holidays
    except ImportError:
        logger.error("holidays library not installed. Install: pip install holidays")
        return {}
    
    try:
        country_holidays = holidays.country_holidays(country, years=year)
        holiday_dict = {}
        
        for date, name in sorted(country_holidays.items()):
            holiday_dict[pd.Timestamp(date)] = name
        
        logger.info(f"Loaded {len(holiday_dict)} holidays for {country} in {year}")
        return holiday_dict
        
    except Exception as e:
        logger.error(f"Failed to load holidays: {e}")
        return {}


def get_holidays_range(start_date: datetime, end_date: datetime, 
                       country: str = "US") -> pd.DataFrame:
    """
    Get holidays for a date range.
    
    Args:
        start_date: Start date
        end_date: End date
        country: Country code
        
    Returns:
        DataFrame with date, holiday_name, and is_holiday columns
    """
    years = set([d.year for d in pd.date_range(start_date, end_date)])
    all_holidays = {}
    
    for year in years:
        all_holidays.update(get_holidays_for_year(year, country))
    
    # Create date range
    date_range = pd.date_range(start_date, end_date, freq='D')
    df = pd.DataFrame({'date': date_range})
    
    # Add holiday information
    df['holiday_name'] = df['date'].map(all_holidays)
    df['is_holiday'] = df['holiday_name'].notna()
    
    logger.info(f"Created holiday calendar: {len(df)} days, {df['is_holiday'].sum()} holidays")
    return df


def compute_holiday_seasonality(holiday_df: pd.DataFrame, 
                               sales_df: Optional[pd.DataFrame] = None) -> Dict[str, float]:
    """
    Compute demand impact during holidays vs non-holidays.
    
    Args:
        holiday_df: DataFrame with is_holiday column
        sales_df: Optional sales data by date for actual impact measurement
        
    Returns:
        Dict with seasonality factors
    """
    factors = {
        "holiday_boost": 1.0,
        "pre_holiday_boost": 1.0,
        "post_holiday_drop": 1.0,
    }
    
    if sales_df is None:
        # Default assumptions based on retail patterns
        logger.info("Using default holiday seasonality factors (no sales data)")
        return {
            "holiday_boost": 1.15,        # +15% demand on holidays
            "pre_holiday_boost": 1.20,    # +20% demand day before
            "post_holiday_drop": 0.90,    # -10% demand after holiday
            "regular_day": 1.0,
        }
    
    # Compute from sales data if provided
    try:
        merged = holiday_df.merge(sales_df, on='date', how='inner')
        
        if merged.empty:
            logger.warning("No matching dates between holidays and sales")
            return factors
        
        # Handle multi-day holidays
        merged['pre_holiday'] = merged['is_holiday'].shift(1).fillna(False)
        merged['post_holiday'] = merged['is_holiday'].shift(-1).fillna(False)
        
        # Compute mean sales by category
        holiday_sales = merged[merged['is_holiday']]['sales'].mean()
        pre_holiday_sales = merged[merged['pre_holiday']]['sales'].mean()
        post_holiday_sales = merged[merged['post_holiday']]['sales'].mean()
        regular_sales = merged[~(merged['is_holiday'] | merged['pre_holiday'] | merged['post_holiday'])]['sales'].mean()
        
        if regular_sales > 0:
            factors = {
                "holiday_boost": holiday_sales / regular_sales if holiday_sales > 0 else 1.0,
                "pre_holiday_boost": pre_holiday_sales / regular_sales if pre_holiday_sales > 0 else 1.0,
                "post_holiday_drop": post_holiday_sales / regular_sales if post_holiday_sales > 0 else 1.0,
                "regular_day": 1.0,
            }
            logger.info(f"Computed holiday factors: {factors}")
        
        return factors
        
    except Exception as e:
        logger.error(f"Failed to compute holiday seasonality: {e}")
        return {
            "holiday_boost": 1.15,
            "pre_holiday_boost": 1.20,
            "post_holiday_drop": 0.90,
            "regular_day": 1.0,
        }


def apply_holiday_seasonality(state_vector: np.ndarray, 
                             current_date: datetime,
                             holiday_df: pd.DataFrame,
                             seasonality_factors: Dict[str, float]) -> np.ndarray:
    """
    Apply holiday seasonality adjustment to state vector.
    
    Args:
        state_vector: Current state features
        current_date: Current date
        holiday_df: Holiday calendar dataframe
        seasonality_factors: Factors from compute_holiday_seasonality
        
    Returns:
        Adjusted state vector
    """
    # Find today in holiday calendar
    today_holiday = holiday_df[holiday_df['date'].dt.date == current_date.date()]
    
    if today_holiday.empty:
        multiplier = seasonality_factors.get("regular_day", 1.0)
    elif today_holiday['is_holiday'].values[0]:
        multiplier = seasonality_factors.get("holiday_boost", 1.15)
    else:
        multiplier = seasonality_factors.get("regular_day", 1.0)
    
    # Apply to demand-related features (indices 4-5: sales_velocity)
    adjusted = state_vector.copy()
    if len(adjusted) > 4:
        adjusted[4] *= multiplier  # sales_velocity_7d
        adjusted[5] *= multiplier  # sales_velocity_30d
    
    return adjusted


def get_major_holidays_in_range(start_date: datetime, end_date: datetime, 
                               country: str = "US") -> List[tuple]:
    """
    Get list of major holidays in a date range.
    
    Args:
        start_date: Start date
        end_date: End date
        country: Country code
        
    Returns:
        List of (date, holiday_name) tuples
    """
    holiday_df = get_holidays_range(start_date, end_date, country)
    major_holidays = [
        (row['date'], row['holiday_name']) 
        for _, row in holiday_df[holiday_df['is_holiday']].iterrows()
    ]
    return major_holidays
