"""Central configuration and environment variables."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./pricing.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # RL Training
    rl_enabled: bool = True
    rl_checkpoint_dir: str = "models/rl_checkpoints"
    rl_update_frequency: int = 3600  # seconds
    
    # ML Models
    prophet_model_path: str = "models/prophet/model.pkl"
    xgboost_model_path: str = "models/xgboost/elasticity.pkl"
    
    # Pricing
    min_price: float = 0.1
    max_price: float = 10000.0
    
    # External APIs
    openmeteo_base_url: str = "https://api.open-meteo.com/v1"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
