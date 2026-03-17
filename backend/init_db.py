"""Initialize the database with tables from models."""
from sqlalchemy import create_engine
from models import Base
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

if __name__ == "__main__":
    init_db()
