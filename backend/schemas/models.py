"""Pydantic models for API schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class ProductBase(BaseModel):
    """Base product schema."""
    name: str
    current_price: float
    cost_price: float


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class Product(ProductBase):
    """Full product schema."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Transaction(BaseModel):
    """Transaction schema."""
    id: str
    product_id: str
    quantity: int
    price: float
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AgentMetrics(BaseModel):
    """RL agent performance metrics."""
    episode: int
    cumulative_reward: float
    average_reward: float
    policy_loss: Optional[float] = None
    timestamp: datetime


class PriceRecommendation(BaseModel):
    """Price recommendation schema."""
    product_id: str
    current_price: float
    recommended_price: float
    confidence: float
    factors: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
