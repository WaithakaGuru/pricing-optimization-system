"""SQLAlchemy ORM models for database."""
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    cost_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = relationship("InventoryItem", back_populates="product")
    transactions = relationship("Transaction", back_populates="product")
    prices = relationship("PriceHistory", back_populates="product")


class InventoryItem(Base):
    """Inventory model."""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String(50), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False)
    reorder_quantity = Column(Integer, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    product = relationship("Product", back_populates="items")


class Transaction(Base):
    """POS transaction model."""
    __tablename__ = "transactions"
    
    id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="transactions")


class PriceHistory(Base):
    """Price change history for analysis."""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(String(50), ForeignKey("products.id"), nullable=False)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    reason = Column(String(100), nullable=True)  # 'rl_recommendation', 'manual', etc
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="prices")


class AgentMetrics(Base):
    """RL agent training metrics."""
    __tablename__ = "agent_metrics"
    
    id = Column(Integer, primary_key=True)
    episode = Column(Integer, nullable=False)
    cumulative_reward = Column(Float, nullable=False)
    average_reward = Column(Float, nullable=True)
    policy_loss = Column(Float, nullable=True)
    value_loss = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
