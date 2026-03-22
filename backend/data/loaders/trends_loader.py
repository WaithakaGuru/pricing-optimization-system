"""Load trend data from Google Trends and compute correlations."""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class TrendsLoader:
    """Load and analyze Google Trends data for demand forecasting."""
    
    def __init__(self, hl: str = 'en-US', tz: int = 360):
        """
        Initialize TrendsLoader.
        
        Args:
            hl: Language/locale (default: 'en-US')
            tz: Timezone offset in minutes (default: 360 = UTC+6)
        """
        self.hl = hl
        self.tz = tz
        self.pytrends = None
        self._initialize_pytrends()
    
    def _initialize_pytrends(self):
        """Initialize pytrends connection."""
        try:
            from pytrends.request import TrendReq
            self.pytrends = TrendReq(hl=self.hl, tz=self.tz)
            logger.info("PyTrends initialized successfully")
        except ImportError:
            logger.error("pytrends not installed. Install: pip install pytrends")
            self.pytrends = None
    
    def fetch_search_trends(self, keyword: str, timeframe: str = "today 1-m") -> pd.DataFrame:
        """
        Fetch Google Trends data for a keyword.
        
        Args:
            keyword: Search term to trend (e.g., "coffee prices", "cell phones")
            timeframe: pytrends timeframe (e.g., 'today 1-m', 'today 3-m', 'today 12-m')
            
        Returns:
            DataFrame with trend data over time
            Columns: [date, interest, keyword]
        """
        if self.pytrends is None:
            logger.error("PyTrends not initialized")
            return pd.DataFrame()
        
        try:
            # Build payload and fetch data
            self.pytrends.build_payload([keyword], timeframe=timeframe)
            trend_data = self.pytrends.interest_over_time()
            
            # Prepare output
            if trend_data.empty:
                logger.warning(f"No trend data found for keyword: {keyword}")
                return pd.DataFrame()
            
            # Rename columns for consistency
            trend_data = trend_data.reset_index()
            trend_data.columns = ['date', 'interest', 'isPartial']
            trend_data = trend_data[['date', 'interest']]
            trend_data['keyword'] = keyword
            
            logger.info(f"✓ Fetched {len(trend_data)} trend data points for '{keyword}'")
            return trend_data
            
        except Exception as e:
            logger.error(f"Error fetching trends for '{keyword}': {e}")
            return pd.DataFrame()
    
    def compute_category_trends(self, category: str, keywords_per_category: int = 3) -> Dict[str, pd.DataFrame]:
        """
        Fetch trends for multiple related keywords.
        
        Args:
            category: Product category (e.g., 'electronics', 'fashion')
            keywords_per_category: Number of keywords to fetch per category
            
        Returns:
            Dict mapping keywords to trend DataFrames
        """
        # Map categories to sample keywords
        category_keywords = {
            "electronics": ["laptop", "smartphone", "tablet"],
            "fashion": ["sneakers", "jacket", "t-shirt"],
            "appliances": ["washing machine", "refrigerator", "microwave"],
            "furniture": ["sofa", "desk", "chair"],
        }
        
        keywords = category_keywords.get(category, [category])[:keywords_per_category]
        
        trends_dict = {}
        for keyword in keywords:
            try:
                trends_df = self.fetch_search_trends(keyword, timeframe="today 1-m")
                if not trends_df.empty:
                    trends_dict[keyword] = trends_df
            except Exception as e:
                logger.warning(f"Could not fetch trends for '{keyword}': {e}")
        
        logger.info(f"✓ Fetched trends for {len(trends_dict)} keywords in category '{category}'")
        return trends_dict
    
    def normalize_trends(self, trend_df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize trend values to [0, 1] range.
        
        Args:
            trend_df: DataFrame with 'interest' column
            
        Returns:
            DataFrame with additional 'interest_normalized' column
        """
        if trend_df.empty:
            return trend_df
        
        df = trend_df.copy()
        
        # Handle all-zero or constant values
        if df['interest'].max() == df['interest'].min():
            df['interest_normalized'] = 0.5  # Middle value if no variation
        else:
            # Min-max normalization to [0, 1]
            min_val = df['interest'].min()
            max_val = df['interest'].max()
            df['interest_normalized'] = (df['interest'] - min_val) / (max_val - min_val)
        
        logger.info(f"✓ Normalized {len(df)} trend values to [0, 1]")
        return df
    
    def compute_trend_momentum(self, trend_df: pd.DataFrame, window: int = 7) -> Dict[str, float]:
        """
        Compute trend momentum (rate of change).
        
        Args:
            trend_df: DataFrame with 'date' and 'interest' columns
            window: Window size for momentum calculation (days)
            
        Returns:
            Dict with momentum metrics:
            - momentum_avg: Average daily change in trend
            - momentum_trend: Overall trend direction (positive = increasing)
            - trend_volatility: Standard deviation of daily changes
        """
        if len(trend_df) < 2:
            return {"momentum_avg": 0.0, "momentum_trend": 0.0, "trend_volatility": 0.0}
        
        df = trend_df.copy().sort_values('date') if 'date' in trend_df.columns else trend_df.copy()
        
        # Compute daily changes
        daily_changes = df['interest'].diff().dropna()
        
        if len(daily_changes) == 0:
            return {"momentum_avg": 0.0, "momentum_trend": 0.0, "trend_volatility": 0.0}
        
        metrics = {
            "momentum_avg": float(daily_changes.mean()),
            "momentum_trend": float(daily_changes[-window:].mean()) if len(daily_changes) >= window else float(daily_changes.mean()),
            "trend_volatility": float(daily_changes.std()),
        }
        
        logger.info(f"✓ Computed momentum: avg={metrics['momentum_avg']:.4f}, trend={metrics['momentum_trend']:.4f}")
        return metrics
    
    def correlate_trends_with_sales(
        self, 
        trends_df: pd.DataFrame, 
        sales_df: pd.DataFrame, 
        max_lag: int = 14
    ) -> Dict[str, float]:
        """
        Measure correlation between trends and sales with potential lag.
        
        Args:
            trends_df: DataFrame with 'date' and 'interest' columns
            sales_df: DataFrame with 'date' and 'sales' columns
            max_lag: Maximum lag to test (days)
            
        Returns:
            Dict with:
            - best_lag: Lag (in days) with highest correlation
            - best_correlation: Correlation coefficient at best lag
            - all_correlations: Dict of lag -> correlation
        """
        if trends_df.empty or sales_df.empty:
            return {
                "best_lag": 0,
                "best_correlation": 0.0,
                "all_correlations": {}
            }
        
        # Merge on date
        trends_df = trends_df.copy().sort_values('date') if 'date' in trends_df.columns else trends_df.copy()
        sales_df = sales_df.copy().sort_values('date') if 'date' in sales_df.columns else sales_df.copy()
        
        merged = pd.merge(trends_df[['date', 'interest']], sales_df[['date', 'sales']], on='date') if 'date' in trends_df.columns and 'date' in sales_df.columns else pd.DataFrame()
        
        if len(merged) < 3:
            return {
                "best_lag": 0,
                "best_correlation": 0.0,
                "all_correlations": {}
            }
        
        # Test different lags
        correlations = {}
        for lag in range(0, min(max_lag + 1, len(merged))):
            if lag == 0:
                corr = merged['interest'].corr(merged['sales'])
            else:
                corr = merged['interest'].iloc[:-lag].corr(merged['sales'].iloc[lag:])
            
            correlations[lag] = corr
        
        # Find best lag
        best_lag = max(correlations.keys(), key=lambda k: abs(correlations[k]))
        best_corr = correlations[best_lag]
        
        logger.info(f"✓ Correlation analysis: best_lag={best_lag}, correlation={best_corr:.4f}")
        
        return {
            "best_lag": best_lag,
            "best_correlation": float(best_corr),
            "all_correlations": {int(k): float(v) for k, v in correlations.items()}
        }


# Backward compatibility: module-level functions
def fetch_search_trends(keyword: str, timeframe: str = "today 1-m") -> pd.DataFrame:
    """Module-level function for backward compatibility."""
    loader = TrendsLoader()
    return loader.fetch_search_trends(keyword, timeframe)


def normalize_trends(trend_df: pd.DataFrame) -> pd.DataFrame:
    """Module-level function for backward compatibility."""
    loader = TrendsLoader()
    return loader.normalize_trends(trend_df)


def compute_trend_momentum(trend_df: pd.DataFrame, window: int = 7) -> Dict[str, float]:
    """Module-level function for backward compatibility."""
    loader = TrendsLoader()
    return loader.compute_trend_momentum(trend_df, window)


def correlate_trends_with_sales(trends_df: pd.DataFrame, sales_df: pd.DataFrame, max_lag: int = 14) -> Dict[str, float]:
    """Module-level function for backward compatibility."""
    loader = TrendsLoader()
    return loader.correlate_trends_with_sales(trends_df, sales_df, max_lag)
