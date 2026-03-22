"""Test suite for TrendsLoader integration."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing TrendsLoader - it may depend on pytrends
try:
    from data.loaders.trends_loader import TrendsLoader
    HAS_PYTRENDS = True
except ImportError as e:
    logger.warning(f"Could not import TrendsLoader: {e}")
    HAS_PYTRENDS = False


class TestTrendsLoaderBasic:
    """Basic tests for TrendsLoader functionality."""

    def test_trends_loader_initialization(self):
        """Test TrendsLoader can be initialized."""
        if not HAS_PYTRENDS:
            pytest.skip("pytrends not available")
        
        loader = TrendsLoader()
        assert loader is not None
        assert hasattr(loader, "fetch_search_trends")
        assert hasattr(loader, "normalize_trends")

    def test_fetch_search_trends(self):
        """Test fetching search trends for a keyword."""
        if not HAS_PYTRENDS:
            pytest.skip("pytrends not available")
        
        loader = TrendsLoader()
        
        # Test with a common search term
        trends_df = loader.fetch_search_trends("laptop", timeframe="today 3-m")
        
        assert trends_df is not None
        assert isinstance(trends_df, pd.DataFrame)
        assert len(trends_df) > 0
        assert "interest" in trends_df.columns.str.lower()
        
        logger.info(f"✓ Fetched {len(trends_df)} data points for 'laptop' search trend")
        logger.info(f"  Interest range: {trends_df['interest'].min()}-{trends_df['interest'].max()}")

    def test_normalize_trends(self):
        """Test trend normalization to [0, 1]."""
        if not HAS_PYTRENDS:
            pytest.skip("pytrends not available")
        
        loader = TrendsLoader()
        
        # Fetch trends
        trends_df = loader.fetch_search_trends("phone", timeframe="today 1-m")
        
        # Normalize
        normalized_df = loader.normalize_trends(trends_df)
        
        assert normalized_df is not None
        assert isinstance(normalized_df, pd.DataFrame)
        assert len(normalized_df) == len(trends_df)
        
        # Check normalization
        if "interest_normalized" in normalized_df.columns:
            assert (normalized_df["interest_normalized"] >= 0).all()
            assert (normalized_df["interest_normalized"] <= 1).all()
            logger.info(f"✓ Normalized {len(normalized_df)} trend values to [0, 1]")

    def test_compute_category_trends(self):
        """Test multi-keyword trend fetching."""
        if not HAS_PYTRENDS:
            pytest.skip("pytrends not available")
        
        loader = TrendsLoader()
        
        # Test with product category
        trends_dict = loader.compute_category_trends("electronics", keywords_per_category=3)
        
        assert trends_dict is not None
        assert isinstance(trends_dict, dict)
        assert len(trends_dict) > 0
        
        for keyword, trends_data in trends_dict.items():
            assert isinstance(trends_data, pd.DataFrame)
            assert len(trends_data) > 0
            logger.info(f"✓ Fetched {len(trends_data)} data points for keyword: '{keyword}'")

    def test_trend_momentum_calculation(self):
        """Test trend momentum computation."""
        if not HAS_PYTRENDS:
            pytest.skip("pytrends not available")
        
        loader = TrendsLoader()
        
        # Create synthetic trend data for testing
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        # Simulating upward trend
        interest_values = np.linspace(20, 80, 30)
        
        test_df = pd.DataFrame({
            "date": dates,
            "interest": interest_values
        })
        
        # Compute momentum
        momentum = loader.compute_trend_momentum(test_df, window=7)
        
        assert momentum is not None
        assert isinstance(momentum, dict)
        assert "momentum_avg" in momentum
        assert "momentum_trend" in momentum
        
        # For upward trend, momentum should be positive
        assert momentum["momentum_avg"] > 0, "Expected positive momentum for upward trend"
        logger.info(f"✓ Computed momentum: {momentum['momentum_avg']:.4f}")

    def test_correlation_with_sales_data(self):
        """Test trend-sales correlation analysis."""
        if not HAS_PYTRENDS:
            pytest.skip("pytrends not available")
        
        loader = TrendsLoader()
        
        # Create synthetic trend and sales data
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        trend_interest = np.sin(np.linspace(0, 2*np.pi, 30)) * 30 + 50  # Oscillating trend
        sales = trend_interest * 100 + np.random.normal(0, 50, 30)  # Correlated with some noise
        
        trends_df = pd.DataFrame({
            "date": dates,
            "interest": trend_interest
        })
        
        sales_df = pd.DataFrame({
            "date": dates,
            "sales": sales
        })
        
        # Compute correlation
        correlations = loader.correlate_trends_with_sales(trends_df, sales_df, max_lag=7)
        
        assert correlations is not None
        assert isinstance(correlations, dict)
        assert "best_lag" in correlations
        assert "best_correlation" in correlations
        
        # Should find significant correlation at lag 0 (same day)
        assert correlations["best_correlation"] > 0.3, "Expected positive correlation"
        logger.info(f"✓ Found correlation: {correlations['best_correlation']:.4f} at lag {correlations['best_lag']}")


class TestTrendsLoaderIntegration:
    """Integration tests for TrendsLoader with RL pipeline."""

    def test_trends_for_state_vector(self):
        """Test extracting trend features for state vector."""
        if not HAS_PYTRENDS:
            pytest.skip("pytrends not available")
        
        loader = TrendsLoader()
        
        # Fetch trends
        trends_df = loader.fetch_search_trends("monitor", timeframe="today 7-d")
        
        # Normalize
        normalized_df = loader.normalize_trends(trends_df)
        
        # Extract most recent value for state vector
        if len(normalized_df) > 0:
            latest_trend = normalized_df.iloc[-1]
            
            if "interest_normalized" in latest_trend:
                trend_value = latest_trend["interest_normalized"]
                assert 0 <= trend_value <= 1, "Trend value should be in [0, 1]"
                logger.info(f"✓ Latest trend value for state vector: {trend_value:.4f}")

    def test_multi_product_trends(self):
        """Test fetching trends for multiple products simultaneously."""
        if not HAS_PYTRENDS:
            pytest.skip("pytrends not available")
        
        loader = TrendsLoader()
        
        # Test multiple product keywords
        products = ["laptop", "desktop", "tablet"]
        all_trends = {}
        
        for product in products:
            try:
                trends_df = loader.fetch_search_trends(product, timeframe="today 1-m")
                normalized_df = loader.normalize_trends(trends_df)
                all_trends[product] = normalized_df
                logger.info(f"✓ Fetched trends for: {product}")
            except Exception as e:
                logger.warning(f"Could not fetch trends for {product}: {e}")
        
        assert len(all_trends) > 0, "Should fetch trends for at least one product"
        logger.info(f"✓ Fetched trends for {len(all_trends)} products")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("TRENDS LOADER TEST SUITE")
    logger.info("=" * 60)
    
    if not HAS_PYTRENDS:
        logger.error("pytrends library not available. Install with: pip install pytrends")
    else:
        # Run tests
        pytest.main([__file__, "-v", "-s"])
