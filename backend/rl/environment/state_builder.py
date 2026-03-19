"""State assembly from multiple signals."""
import numpy as np
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Product, InventoryItem, Transaction
from datetime import datetime, timedelta

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

    def __init__(self, config: dict = None, db_url: str = "sqlite:///pricing.db"):
        """
        Initialize state builder.
        
        Args:
            config: Optional configuration dict
            db_url: Database URL for fetching data
        """
        self.config = config or {}
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
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
        from backend.models import PriceHistory
        
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
        Placeholder: use day-of-year for simplistic seasonality.
        """
        day_of_year = datetime.utcnow().timetuple().tm_yday
        # Simple sine wave for seasonality
        import math
        return math.sin(2 * math.pi * day_of_year / 365.0)

    def _get_weather_factor(self) -> float:
        """
        Get weather factor (-1 to 1).
        Placeholder: returns 0 (neutral).
        TODO: Integrate with Open-Meteo API for real weather data.
        """
        return 0.0

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
