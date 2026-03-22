"""Price recommendation endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from services.pricing_service import PricingService
from services.weather_service import WeatherService
from utils.logger import get_logger
from models import get_session, Product, PriceHistory

logger = get_logger(__name__)
router = APIRouter(prefix="/api/prices", tags=["prices"])


class PriceRecommendation(BaseModel):
    """Price recommendation response."""
    product_id: str
    current_price: float
    recommended_price: float
    confidence: float
    agent: str
    factors: dict
    weather_impact: Optional[dict] = None  # NEW: Weather contribution
    timestamp: str


class ApplyPriceRequest(BaseModel):
    """Request to apply a new price."""
    price: float
    reason: Optional[str] = "user_adjustment"


class PriceHistoryEntry(BaseModel):
    """Price history entry."""
    date: str
    price: float
    reason: str


@router.get("/recommend/{product_id}", response_model=PriceRecommendation)
async def get_price_recommendation(
    product_id: str,
    agent_type: str = Query("ppo", description="Agent type: ppo, sac, or bandit"),
    include_weather: bool = Query(True, description="Include weather impact analysis")
) -> PriceRecommendation:
    """
    Get AI-powered price recommendation for a product.
    
    - **product_id**: The product identifier
    - **agent_type**: Type of agent to use (ppo, sac, bandit)
    - **include_weather**: Include weather impact in response (default: true)
    
    Returns a recommendation with confidence score and explanation factors.
    """
    try:
        # Validate agent type
        if agent_type not in ["ppo", "sac", "bandit"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent_type. Must be one of: ppo, sac, bandit"
            )
        
        # Initialize pricing service with specified agent
        logger.info(f"Getting recommendation for {product_id} using {agent_type} agent")
        service = PricingService(agent_type=agent_type)
        
        # Get recommendation
        recommendation = service.get_recommendation(product_id)
        
        if not recommendation:
            raise HTTPException(
                status_code=404,
                detail=f"Could not generate recommendation for product {product_id}"
            )
        
        # Get weather data if requested
        weather_impact = None
        if include_weather:
            try:
                weather_service = WeatherService()
                weather_data = await weather_service.get_weather_for_state()
                
                if weather_data:
                    # Compute weather impact on this product
                    weather_type = weather_data.get("weather_type", "unknown")
                    precipitation = weather_data.get("precipitation", 0.0)
                    temperature = weather_data.get("temperature", 0.5)
                    
                    # Estimate demand impact percentage
                    weather_impact_pct = 0.0
                    if weather_type == "rain":
                        weather_impact_pct = -15.0  # -15% demand
                    elif weather_type == "clear":
                        weather_impact_pct = 10.0  # +10% demand
                    elif weather_type == "cloudy":
                        weather_impact_pct = 0.0  # Neutral
                    elif weather_type == "snow":
                        weather_impact_pct = -25.0  # -25% demand
                    
                    weather_impact = {
                        "temperature": round(weather_data.get("temperature", 0) * 50 - 10, 1),  # Denormalize back to Celsius
                        "weather_type": weather_type,
                        "precipitation_mm": round(precipitation * 50, 1),  # Denormalize back to mm
                        "demand_impact_pct": weather_impact_pct,
                        "note": f"Weather factor: {weather_type}. Estimated demand impact: {weather_impact_pct:+.1f}%"
                    }
                    logger.info(f"Weather impact computed for {product_id}: {weather_impact_pct:+.1f}%")
                
                await weather_service.close()
            except Exception as e:
                logger.warning(f"Could not fetch weather data: {e}")
                # Continue without weather data
        
        return PriceRecommendation(
            product_id=recommendation["product_id"],
            current_price=recommendation["current_price"],
            recommended_price=recommendation["recommended_price"],
            confidence=recommendation["confidence"],
            agent=recommendation["agent"],
            factors=recommendation["factors"],
            weather_impact=weather_impact,
            timestamp=recommendation["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price recommendation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply/{product_id}", response_model=dict)
async def apply_price(product_id: str, request: ApplyPriceRequest) -> dict:
    """
    Apply a new price to a product and record in database.
    
    - **product_id**: The product identifier
    - **request**: Contains new price and reason for change
    
    Updates the product's base price and creates a PriceHistory record.
    """
    try:
        logger.info(f"Applying price ${request.price} to {product_id}")
        service = PricingService(agent_type="ppo")
        
        # Apply price via service
        result = service.apply_price(
            product_id,
            request.price,
            applied_by=request.reason
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Product {product_id} not found"
            )
        
        logger.info(f"Successfully applied price for {product_id}")
        return {
            "success": True,
            "product_id": product_id,
            "new_price": request.price,
            "applied_at": datetime.utcnow().isoformat(),
            "reason": request.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying price: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{product_id}", response_model=list[PriceHistoryEntry])
async def get_price_history(
    product_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve")
) -> list[PriceHistoryEntry]:
    """
    Get historical price changes for a product.
    
    - **product_id**: The product identifier
    - **days**: Number of days of history to retrieve (default: 30, max: 365)
    
    Returns list of price changes with dates and reasons.
    """
    try:
        session = get_session()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query price history
        history = session.query(PriceHistory).filter(
            PriceHistory.product_id == product_id,
            PriceHistory.created_at >= start_date,
            PriceHistory.created_at <= end_date
        ).order_by(PriceHistory.created_at.desc()).all()
        
        session.close()
        
        if not history:
            logger.warning(f"No price history found for {product_id}")
            return []
        
        return [
            PriceHistoryEntry(
                date=h.created_at.isoformat(),
                price=h.new_price,
                reason=h.reason or "adjustment"
            )
            for h in history
        ]
        
    except Exception as e:
        logger.error(f"Error fetching price history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current/{product_id}", response_model=dict)
async def get_current_price(product_id: str) -> dict:
    """
    Get the current price of a product.
    
    - **product_id**: The product identifier
    """
    try:
        session = get_session()
        product = session.query(Product).filter(Product.id == product_id).first()
        session.close()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        return {
            "product_id": product.id,
            "name": product.name,
            "current_price": float(product.base_price),
            "cost_price": float(product.cost_price),
            "margin_pct": ((product.base_price - product.cost_price) / product.base_price * 100)
                if product.base_price > 0 else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current price: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
