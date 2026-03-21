"""Reset database with correct schema and add sample data."""
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Transaction, InventoryItem, PriceHistory, AgentMetrics
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///pricing.db"

def reset_db():
    """Drop and recreate all tables."""
    # Remove old database if it exists
    if os.path.exists("pricing.db"):
        os.remove("pricing.db")
        logger.info("🗑️  Removed old database")
    
    # Create engine and tables
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    logger.info("✅ Database schema created successfully!")
    
    return engine


def seed_products(session):
    """Seed sample products."""
    logger.info("🌱 Seeding products...")
    
    sample_products = [
        Product(
            id='p001',
            name='Arabica Coffee Beans 1kg',
            cost_price=8.50,
            min_price=12,
            max_price=28,
            current_price=18.99,
        ),
        Product(
            id='p002',
            name='Organic Green Tea 200g',
            cost_price=4.20,
            min_price=7,
            max_price=18,
            current_price=11.50,
        ),
        Product(
            id='p003',
            name='Cold Brew Concentrate 500ml',
            cost_price=5.80,
            min_price=9,
            max_price=20,
            current_price=14.99,
        ),
        Product(
            id='p004',
            name='Matcha Powder Premium 100g',
            cost_price=11.00,
            min_price=18,
            max_price=40,
            current_price=24.99,
        ),
        Product(
            id='p005',
            name='Herbal Chamomile Mix 50g',
            cost_price=2.10,
            min_price=4,
            max_price=12,
            current_price=7.49,
        ),
        Product(
            id='p006',
            name='Espresso Roast Dark 500g',
            cost_price=7.20,
            min_price=11,
            max_price=24,
            current_price=16.99,
        ),
    ]
    
    session.add_all(sample_products)
    session.commit()
    logger.info(f"✅ Added {len(sample_products)} products")
    
    return sample_products


def seed_inventory(session, products):
    """Seed inventory items."""
    logger.info("📦 Seeding inventory...")
    
    now = datetime.utcnow()
    restock_date = now - timedelta(days=random.randint(1, 15))
    
    warehouse_locations = ["Main Warehouse", "Cold Storage", "Display Floor", "Stock Room A", "Stock Room B"]
    
    inventory_items = [
        InventoryItem(product_id='p001', quantity=150, reorder_point=50, reorder_quantity=100, last_restock_date=restock_date, warehouse_location=random.choice(warehouse_locations)),
        InventoryItem(product_id='p002', quantity=200, reorder_point=75, reorder_quantity=150, last_restock_date=restock_date, warehouse_location=random.choice(warehouse_locations)),
        InventoryItem(product_id='p003', quantity=85, reorder_point=30, reorder_quantity=60, last_restock_date=restock_date, warehouse_location=random.choice(warehouse_locations)),
        InventoryItem(product_id='p004', quantity=45, reorder_point=20, reorder_quantity=40, last_restock_date=restock_date, warehouse_location=random.choice(warehouse_locations)),
        InventoryItem(product_id='p005', quantity=220, reorder_point=100, reorder_quantity=200, last_restock_date=restock_date, warehouse_location=random.choice(warehouse_locations)),
        InventoryItem(product_id='p006', quantity=110, reorder_point=40, reorder_quantity=80, last_restock_date=restock_date, warehouse_location=random.choice(warehouse_locations)),
    ]
    
    session.add_all(inventory_items)
    session.commit()
    logger.info(f"✅ Added {len(inventory_items)} inventory items")


def seed_transactions(session):
    """Seed sample transactions with realistic data."""
    logger.info("💳 Seeding transactions...")
    
    product_ids = ['p001', 'p002', 'p003', 'p004', 'p005', 'p006']
    payment_methods = ['cash', 'card', 'mobile']
    
    # Generate transactions over the last 30 days
    transactions = []
    now = datetime.utcnow()
    
    for i in range(50):  # Create 50 transactions
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # Create transaction
        product_id = random.choice(product_ids)
        quantity = random.randint(1, 5)
        
        # Prices vary slightly
        prices = {
            'p001': 18.99,
            'p002': 11.50,
            'p003': 14.99,
            'p004': 24.99,
            'p005': 7.49,
            'p006': 16.99,
        }
        
        price = prices[product_id] + random.uniform(-2, 2)
        total = quantity * price
        
        transaction = Transaction(
            id=f"txn_{uuid.uuid4().hex[:10]}",
            product_id=product_id,
            quantity=quantity,
            price=price,
            revenue=total,
            total=total,  # This is the key field that was missing!
            payment_method=random.choice(payment_methods),
            notes=random.choice([None, "Bulk order", "Customer special", "Trial", None]),
            timestamp=timestamp
        )
        transactions.append(transaction)
    
    session.add_all(transactions)
    session.commit()
    logger.info(f"✅ Added {len(transactions)} transactions")


def seed_agent_metrics(session):
    """Seed agent metrics for dashboard."""
    logger.info("🤖 Seeding agent metrics...")
    
    metrics = []
    now = datetime.utcnow()
    
    for i in range(20):
        days_ago = random.randint(0, 30)
        timestamp = now - timedelta(days=days_ago)
        
        metric = AgentMetrics(
            episode=i,
            cumulative_reward=random.uniform(100, 500),
            average_reward=random.uniform(50, 150),
            policy_loss=random.uniform(0.01, 0.5),
            value_loss=random.uniform(0.05, 1.0),
            reward=random.choice([1.0, 0.0]),
            confidence=random.uniform(0.5, 0.95),
            applied=random.choice([True, False]),
            revenue_impact=random.uniform(-5, 15),
            timestamp=timestamp
        )
        metrics.append(metric)
    
    session.add_all(metrics)
    session.commit()
    logger.info(f"✅ Added {len(metrics)} agent metrics")


def main():
    """Reset and seed database."""
    logger.info("=" * 50)
    logger.info("🚀 RESETTING AND SEEDING DATABASE")
    logger.info("=" * 50)
    
    # Reset database
    engine = reset_db()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Seed all data
        products = seed_products(session)
        seed_inventory(session, products)
        seed_transactions(session)
        seed_agent_metrics(session)
        
        logger.info("=" * 50)
        logger.info("✅ DATABASE SETUP COMPLETE!")
        logger.info("=" * 50)
        logger.info("✓ Products seeded")
        logger.info("✓ Inventory seeded")
        logger.info("✓ Transactions seeded (with 'total' column)")
        logger.info("✓ Agent metrics seeded")
        logger.info("")
        logger.info("You can now run the application and see data on the frontend!")
        
    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
