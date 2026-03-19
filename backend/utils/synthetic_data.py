"""Synthetic data generator for bootstrap training without real data."""
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

np.random.seed(42)  # Reproducible results


def generate_synthetic_sales(
    num_products: int = 10,
    num_days: int = 90,
    price_elasticity: float = -0.5,
) -> pd.DataFrame:
    """
    Generate synthetic sales data with realistic price elasticity.
    
    Model: demand = base_demand * (price / base_price)^elasticity + noise + seasonality
    
    Args:
        num_products: Number of products to simulate
        num_days: Number of days of data
        price_elasticity: Price elasticity of demand (default -0.5, typical for retail)
        
    Returns:
        DataFrame with columns:
            - date: Transaction date
            - product_id: Product identifier
            - price: Price at transaction
            - quantity_sold: Units sold
            - revenue: price * quantity_sold
            - cost_price: Cost (fixed per product)
    """
    data = []
    
    for product_idx in range(num_products):
        product_id = f"PROD-{product_idx+1:03d}"
        
        # Product-specific parameters
        base_price = np.random.uniform(5, 50)  # Base price $5-$50
        cost_price = base_price * np.random.uniform(0.4, 0.6)  # Cost 40-60% of price
        base_demand = np.random.uniform(20, 100)  # 20-100 units per day baseline
        
        # Generate time series
        for day in range(num_days):
            date = datetime.utcnow() - timedelta(days=num_days - day)
            
            # Price varies slightly over time (±10% of base)
            price_factor = np.random.uniform(0.9, 1.1)
            price = base_price * price_factor
            
            # Demand components
            # 1. Base demand
            demand = base_demand
            
            # 2. Price elasticity effect
            price_effect = (price / base_price) ** price_elasticity
            demand *= price_effect
            
            # 3. Seasonality (weekly pattern: high on weekends)
            day_of_week = (date.weekday() + 1) % 7
            seasonality = 0.8 + 0.4 * math.sin(2 * math.pi * day_of_week / 7)
            demand *= seasonality
            
            # 4. Random noise
            noise = np.random.normal(1.0, 0.15)  # Normal dist, 15% std dev
            demand *= noise
            
            # Ensure non-negative
            quantity_sold = max(0, int(demand))
            revenue = price * quantity_sold
            
            if quantity_sold > 0:  # Only log if there's a sale
                data.append({
                    "date": date,
                    "product_id": product_id,
                    "price": round(price, 2),
                    "quantity_sold": quantity_sold,
                    "revenue": round(revenue, 2),
                    "cost_price": round(cost_price, 2),
                })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} synthetic sales transactions for {num_products} products over {num_days} days")
    return df.sort_values("date").reset_index(drop=True)


def generate_synthetic_inventory(
    num_products: int = 10,
    num_days: int = 90,
) -> pd.DataFrame:
    """
    Generate synthetic inventory data with realistic stock movements.
    
    Model: Inventory depletes with sales, gets restocked at reorder points.
    
    Args:
        num_products: Number of products
        num_days: Number of days
        
    Returns:
        DataFrame with columns:
            - date: Date
            - product_id: Product ID
            - stock_level: Units in stock
            - reorder_point: Threshold to trigger reorder
            - was_restocked: Boolean, was inventory replenished today
    """
    data = []
    
    for product_idx in range(num_products):
        product_id = f"PROD-{product_idx+1:03d}"
        
        # Product parameters
        initial_stock = np.random.randint(50, 300)
        daily_demand = np.random.uniform(10, 50)
        reorder_point = int(daily_demand * np.random.uniform(5, 10))  # 5-10 days of stock
        restock_quantity = int(daily_demand * np.random.uniform(20, 40))  # 20-40 days of stock
        
        stock = initial_stock
        
        for day in range(num_days):
            date = datetime.utcnow() - timedelta(days=num_days - day)
            
            # Random daily depletion
            daily_depletion = int(np.random.normal(daily_demand, daily_demand * 0.2))
            daily_depletion = max(0, daily_depletion)
            
            # Deplete stock
            stock = max(0, stock - daily_depletion)
            
            # Check if reorder needed
            was_restocked = False
            if stock <= reorder_point:
                stock += restock_quantity
                was_restocked = True
            
            data.append({
                "date": date,
                "product_id": product_id,
                "stock_level": stock,
                "reorder_point": reorder_point,
                "was_restocked": was_restocked,
            })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} synthetic inventory records for {num_products} products")
    return df


def generate_synthetic_weather(
    latitude: float = 40.7128,
    longitude: float = -74.0060,
    num_days: int = 90,
) -> pd.DataFrame:
    """
    Generate synthetic weather data with realistic patterns.
    
    Includes seasonality, daily patterns, random perturbations.
    
    Args:
        latitude: Location latitude (for seasonal variation)
        longitude: Location longitude
        num_days: Number of days
        
    Returns:
        DataFrame with columns:
            - date: Date
            - temperature: Average daily temp in Celsius
            - humidity: Humidity %
            - precipitation: Daily precipitation in mm
            - cloud_cover: Cloud cover %
    """
    current_temp = 15 + 10 * math.sin(2 * math.pi * latitude / 90)  # Latitude-based baseline
    
    data = []
    for day in range(num_days):
        date = datetime.utcnow() - timedelta(days=num_days - day)
        day_of_year = date.timetuple().tm_yday
        
        # Baseline temperature with annual seasonality
        seasonal_temp = current_temp + 15 * math.sin(2 * math.pi * day_of_year / 365)
        
        # Daily variation (cooler at night, warmer during day on average)
        daily_variation = 8 * math.sin(2 * math.pi * date.hour / 24) if hasattr(date, 'hour') else 0
        
        # Random weather noise
        temp_noise = np.random.normal(0, 2)
        temperature = seasonal_temp + daily_variation + temp_noise
        
        # Humidity (inversely correlated with temperature roughly)
        humidity = 50 + 30 * math.sin(2 * math.pi * day_of_year / 365) + np.random.normal(0, 5)
        humidity = np.clip(humidity, 20, 95)
        
        # Precipitation (more likely when humidity is high)
        precip_prob = (humidity - 50) / 100
        precipitation = 0.0
        if np.random.random() < precip_prob:
            precipitation = np.random.exponential(5)  # mm, exponential distribution
        
        # Cloud cover
        cloud_cover = 30 + 40 * math.sin(2 * math.pi * day_of_year / 365) + np.random.normal(0, 15)
        cloud_cover = np.clip(cloud_cover, 0, 100)
        
        data.append({
            "date": date,
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "precipitation": round(precipitation, 1),
            "cloud_cover": round(cloud_cover, 1),
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} synthetic weather records")
    return df


def create_product_master(num_products: int = 10) -> pd.DataFrame:
    """
    Create product master data.
    
    Args:
        num_products: Number of products
        
    Returns:
        DataFrame with product metadata
    """
    products = []
    for i in range(num_products):
        product_id = f"PROD-{i+1:03d}"
        base_price = np.random.uniform(5, 50)
        cost_price = base_price * np.random.uniform(0.4, 0.6)
        
        products.append({
            "product_id": product_id,
            "name": f"Product {i+1}",
            "base_price": round(base_price, 2),
            "cost_price": round(cost_price, 2),
            "min_price": round(base_price * 0.5, 2),
            "max_price": round(base_price * 1.5, 2),
            "category": np.random.choice(["Electronics", "Clothing", "Food", "Home"]),
        })
    
    return pd.DataFrame(products)


def load_synthetic_data_into_db(db_url: str = "sqlite:///pricing.db"):
    """
    Load synthetic data into the database.
    
    Populates Product, InventoryItem, Transaction tables with synthetic data for testing.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.models import Product, InventoryItem, Transaction
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    logger.info("Loading synthetic data into database...")
    
    # Generate data
    sales_df = generate_synthetic_sales(num_products=5, num_days=30)
    inventory_df = generate_synthetic_inventory(num_products=5, num_days=30)
    products_df = create_product_master(num_products=5)
    
    # Load products
    for _, row in products_df.iterrows():
        product = session.query(Product).filter(Product.id == row["product_id"]).first()
        if not product:
            product = Product(
                id=row["product_id"],
                name=row["name"],
                cost_price=row["cost_price"],
                min_price=row["min_price"],
                max_price=row["max_price"],
                current_price=row["base_price"],
            )
            session.add(product)
    
    session.commit()
    logger.info(f"Loaded {len(products_df)} products")
    
    # Load inventory
    for product_id in products_df["product_id"]:
        latest_inv = inventory_df[inventory_df["product_id"] == product_id].iloc[-1]
        
        inventory = session.query(InventoryItem).filter(
            InventoryItem.product_id == product_id
        ).first()
        
        if not inventory:
            inventory = InventoryItem(
                product_id=product_id,
                quantity=int(latest_inv["stock_level"]),
                reorder_point=int(latest_inv["reorder_point"]),
                reorder_quantity=int(latest_inv["reorder_point"] * 2),
            )
            session.add(inventory)
    
    session.commit()
    logger.info(f"Loaded inventory for {len(products_df)} products")
    
    # Load transactions
    for _, row in sales_df.iterrows():
        transaction = Transaction(
            id=f"TXN-{row['date'].timestamp()}-{row['product_id']}",
            product_id=row["product_id"],
            quantity=row["quantity_sold"],
            price=row["price"],
            revenue=row["revenue"],
            timestamp=row["date"],
        )
        session.add(transaction)
    
    session.commit()
    logger.info(f"Loaded {len(sales_df)} transactions")
    session.close()
    logger.info("✅ Synthetic data loaded successfully!")

generate_synthetic_sales()
generate_synthetic_weather()