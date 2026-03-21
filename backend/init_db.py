"""Initialize the database with tables from models."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLite for local development
DATABASE_URL = "sqlite:///pricing.db"

def init_db():
    """Create all tables in the database."""
    engine = create_engine(DATABASE_URL, echo=True)
    
    logger.info(f"Creating database at {DATABASE_URL}")
    Base.metadata.create_all(engine)
    logger.info("✅ Database initialized successfully!")
    logger.info("Tables created: Product, InventoryItem, Transaction, PriceHistory, AgentMetrics")
    
    # Seed sample products
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if products already exist
    existing_count = session.query(Product).count()
    if existing_count == 0:
        logger.info("Seeding database with sample products...")
        
        sample_products = [
            Product(
                id='p001',
                name='Arabica Coffee Beans 1kg',
                cost_price=8.50,
                min_price=12,
                max_price=28,
                current_price=18.99,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Product(
                id='p002',
                name='Organic Green Tea 200g',
                cost_price=4.20,
                min_price=7,
                max_price=18,
                current_price=11.50,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Product(
                id='p003',
                name='Cold Brew Concentrate 500ml',
                cost_price=5.80,
                min_price=9,
                max_price=20,
                current_price=14.99,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Product(
                id='p004',
                name='Matcha Powder Premium 100g',
                cost_price=11.00,
                min_price=18,
                max_price=40,
                current_price=24.99,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Product(
                id='p005',
                name='Herbal Chamomile Mix 50g',
                cost_price=2.10,
                min_price=4,
                max_price=12,
                current_price=7.49,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Product(
                id='p006',
                name='Espresso Roast Dark 500g',
                cost_price=7.20,
                min_price=11,
                max_price=24,
                current_price=16.99,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
        ]
        
        session.add_all(sample_products)
        session.commit()
        logger.info(f"✅ Seeded {len(sample_products)} products")
    else:
        logger.info(f"Database already has {existing_count} products, skipping seed")
    
    session.close()

if __name__ == "__main__":
    init_db()
