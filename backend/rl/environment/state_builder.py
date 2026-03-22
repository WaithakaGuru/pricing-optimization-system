"""State assembly from multiple signals."""
import numpy as np
import logging
import sys
import asyncio
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Fix import paths for module resolution
_backend_path = Path(__file__).parent.parent.parent / "backend"
if str(_backend_path) not in sys.path:
    sys.path.insert(0, str(_backend_path))

try:
    from models import Product, InventoryItem, Transaction
    from services.weather_service import WeatherService
except ImportError:
    # If direct import fails, try relative from parent backend package
    import importlib.util
    models_path = Path(__file__).parent.parent.parent / "backend" / "models.py"
    spec = importlib.util.spec_from_file_location("models", models_path)
    models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models)
    Product = models.Product
    InventoryItem = models.InventoryItem
    Transaction = models.Transaction
    
    # Import weather service
    weather_path = Path(__file__).parent.parent.parent / "backend" / "services" / "weather_service.py"
    spec_weather = importlib.util.spec_from_file_location("weather_service", weather_path)
    weather_module = importlib.util.module_from_spec(spec_weather)
    spec_weather.loader.exec_module(weather_module)
    WeatherService = weather_module.WeatherService

logger = logging.getLogger(__name__)


class StateBuilder:
    """
    Assembles RL state from:
    - Product features (current price, cost, profit margin)
    - Demand signals (sales velocity, recent transactions)
    - Inventory (stock level, turnover rate)
    - External signals (weather, trends, seasonality)
    
    State vector has 12 dimensions:
    [current_price, cost_price, margin%, inventory_level, 
     sales_velocity_7d, sales_velocity_30d, inventory_turnover,
     price_trend, demand_trend, seasonality, weather_factor, competitor_factor]
    """

    def __init__(self, config: dict = None, db_url: str = "sqlite:///pricing.db", 
                 latitude: float = 40.7128, longitude: float = -74.0060):
        """
        Initialize state builder.
        
        Args:
            config: Optional configuration dict
            db_url: Database URL for fetching data
            latitude: Location latitude for weather data (default NYC)
            longitude: Location longitude for weather data (default NYC)
        """
        self.config = config or {}
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize weather service
        self.weather_service = WeatherService(latitude=latitude, longitude=longitude)
        self._weather_data_cache = None
        self._weather_data_timestamp = None
        
        self.feature_names = [
            "current_price",
            "cost_price",
            "margin_pct",
            "inventory_level",
            "sales_velocity_7d",
            "sales_velocity_30d",
            "inventory_turnover",
            "price_trend",
            "demand_trend",
            "seasonality_factor",
            "weather_factor",
            "competitor_factor"
        ]
        
        # Normalization parameters (min, max for each feature)
        self.normalization_bounds = {
            "current_price": (0.1, 1000.0),
            "cost_price": (0.05, 500.0),
            "margin_pct": (0.0, 100.0),
            "inventory_level": (0, 10000),
            "sales_velocity_7d": (0, 100),
            "sales_velocity_30d": (0, 500),
            "inventory_turnover": (0, 10),
            "price_trend": (-1, 1),
            "demand_trend": (-1, 1),
            "seasonality_factor": (-1, 1),
            "weather_factor": (-1, 1),
            "competitor_factor": (-1, 1),
        }

    def build_state(self, product_id: str) -> np.ndarray:
        """
        Build complete state vector for a product.
        
        Args:
            product_id: The product identifier
            
        Returns:
            Normalized state vector as numpy array (shape: 12,)
        """
        try:
            session = self.Session()
            
            # Fetch product data
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                logger.warning(f"Product {product_id} not found")
                return self._default_state()
            
            # Fetch inventory data
            inventory = session.query(InventoryItem).filter(
                InventoryItem.product_id == product_id
            ).first()
            
            # Calculate demand signals
            sales_7d = self._calculate_sales_velocity(session, product_id, days=7)
            sales_30d = self._calculate_sales_velocity(session, product_id, days=30)
            
            # Build features dict
            features = {
                "current_price": product.current_price,
                "cost_price": product.cost_price,
                "margin_pct": ((product.current_price - product.cost_price) / product.current_price * 100) if product.current_price > 0 else 0,
                "inventory_level": inventory.quantity if inventory else 0,
                "sales_velocity_7d": sales_7d,
                "sales_velocity_30d": sales_30d,
                "inventory_turnover": self._calculate_inventory_turnover(session, product_id, inventory),
                "price_trend": self._calculate_price_trend(session, product_id),
                "demand_trend": self._calculate_demand_trend(sales_7d, sales_30d),
                "seasonality_factor": self._get_seasonality_factor(),
                "weather_factor": self._get_weather_factor(),  # Placeholder
                "competitor_factor": self._get_competitor_factor(),  # Placeholder
            }
            
            session.close()
            
            # Normalize and convert to array
            normalized = self._normalize_features(features)
            state_array = np.array(normalized, dtype=np.float32)
            
            logger.debug(f"Built state for {product_id}: {state_array}")
            return state_array
            
        except Exception as e:
            logger.error(f"Error building state for {product_id}: {e}")
            return self._default_state()

    def _calculate_sales_velocity(self, session, product_id: str, days: int = 7) -> float:
        """Calculate number of sales in the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count = session.query(Transaction).filter(
            Transaction.product_id == product_id,
            Transaction.timestamp >= cutoff_date
        ).count()
        return float(count)

    def _calculate_inventory_turnover(self, session, product_id: str, inventory) -> float:
        """
        Calculate inventory turnover rate.
        Turnover = sales_30d / avg_inventory
        """
        if not inventory or inventory.quantity == 0:
            return 0.0
        sales_30d = self._calculate_sales_velocity(session, product_id, days=30)
        turnover = sales_30d / inventory.quantity if inventory.quantity > 0 else 0.0
        return min(turnover, 10.0)  # Cap at 10

    def _calculate_price_trend(self, session, product_id: str) -> float:
        """
        Calculate price trend (-1 to 1).
        -1 = prices falling, 0 = stable, 1 = prices rising
        """
        from models import PriceHistory
        
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        price_changes = session.query(PriceHistory).filter(
            PriceHistory.product_id == product_id,
            PriceHistory.timestamp >= cutoff_date
        ).all()
        
        if len(price_changes) < 2:
            return 0.0
        
        # Compare first and last price
        first_price = price_changes[0].old_price
        last_price = price_changes[-1].new_price
        
        if first_price == 0:
            return 0.0
        
        pct_change = (last_price - first_price) / first_price
        return max(-1.0, min(1.0, pct_change))  # Bound to [-1, 1]

    def _calculate_demand_trend(self, sales_7d: float, sales_30d: float) -> float:
        """
        Calculate demand trend.
        Compare recent 7-day sales to 30-day average.
        """
        if sales_30d == 0:
            return 0.0
        avg_30d = sales_30d / 4.3  # ~4.3 weeks in 30 days
        if avg_30d == 0:
            return 0.0
        pct_change = (sales_7d - avg_30d) / avg_30d
        return max(-1.0, min(1.0, pct_change))

    def _get_seasonality_factor(self) -> float:
        """
        Get seasonality factor (-1 to 1).
        Uses day-of-year for simplistic seasonality.
        """
        day_of_year = datetime.utcnow().timetuple().tm_yday
        # Simple sine wave for seasonality
        import math
        return math.sin(2 * math.pi * day_of_year / 365.0)

    async def _get_weather_factor_async(self) -> float:
        """
        Get weather factor (-1 to 1) from Open-Meteo API.
        
        Weather impact on demand:
        - Clear/warm: +0.5 (comfortable shopping)
        - Rain/cold: -0.5 (reduced foot traffic)
        - Moderate temps: 0 (neutral)
        
        Returns:
            Weather factor in range [-1, 1]
        """
        try:
            weather_data = await self.weather_service.get_weather_for_state()
            
            if not weather_data:
                logger.warning("Weather data unavailable, using neutral factor")
                return 0.0
            
            # Temperature impact: ideal range [18-24°C]
            temp_norm = weather_data.get("temperature", 0.5)  # Already normalized [0, 1]
            temp_factor = 1.0 - abs(temp_norm - 0.5) * 2  # Peak at mid-range
            
            # Precipitation impact: negative for rain
            precip_norm = weather_data.get("precipitation", 0.0)
            precip_factor = -precip_norm  # Negative impact
            
            # Weather type modifier
            weather_type = weather_data.get("weather_type", "clear")
            type_modifiers = {
                "clear": 0.3,
                "cloudy": 0.0,
                "foggy": -0.2,
                "drizzle": -0.1,
                "rain": -0.3,
                "snow": -0.5,
                "storm": -0.8,
            }
            type_factor = type_modifiers.get(weather_type, 0.0)
            
            # Combine factors
            weather_factor = (temp_factor * 0.4 + precip_factor * 0.3 + type_factor * 0.3)
            weather_factor = max(-1.0, min(1.0, weather_factor))  # Clamp to [-1, 1]
            
            logger.debug(f"Weather factor computed: {weather_factor:.2f} (temp={temp_norm:.2f}, precip={precip_norm:.2f}, type={weather_type})")
            return weather_factor
            
        except Exception as e:
            logger.warning(f"Failed to compute weather factor: {e}, using neutral")
            return 0.0

    def _get_weather_factor(self) -> float:
        """
        Get weather factor synchronously (wrapper for async method).
        
        This is used when building state in non-async contexts.
        Falls back to cached value if available, otherwise returns neutral.
        """
        # Check cache validity (5 minute TTL)
        if self._weather_data_timestamp:
            cache_age = (datetime.utcnow() - self._weather_data_timestamp).total_seconds()
            if cache_age < 300:  # 5 minutes
                return self._weather_data_cache or 0.0
        
        # Try to get fresh data asynchronously
        try:
            # Create new event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # Can't run async in a running loop, use cached value
                logger.debug("Event loop running, using cached weather data")
                return self._weather_data_cache or 0.0
            
            factor = loop.run_until_complete(self._get_weather_factor_async())
            self._weather_data_cache = factor
            self._weather_data_timestamp = datetime.utcnow()
            return factor
            
        except Exception as e:
            logger.debug(f"Could not fetch weather factor asynchronously: {e}")
            return self._weather_data_cache or 0.0

    def _get_competitor_factor(self) -> float:
        """
        Get competitor price factor (-1 to 1).
        Placeholder: returns 0 (neutral).
        TODO: Integrate with competitor price data when available.
        """
        return 0.0

    def _normalize_features(self, features: dict) -> list:
        """
        Normalize features using min-max scaling.
        
        Converts each feature to [0, 1] range based on bounds.
        """
        normalized = []
        for name in self.feature_names:
            value = features.get(name, 0.0)
            min_val, max_val = self.normalization_bounds[name]
            
            if max_val == min_val:
                normalized_value = 0.5
            else:
                normalized_value = (value - min_val) / (max_val - min_val)
                normalized_value = max(0.0, min(1.0, normalized_value))  # Clamp to [0, 1]
            
            normalized.append(normalized_value)
        
        return normalized

    def _default_state(self) -> np.ndarray:
        """Return a default neutral state."""
        return np.array([0.5] * len(self.feature_names), dtype=np.float32)
