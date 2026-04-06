"""Price recommendation endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from pathlib import Path
from services.pricing_service import PricingService
from services.weather_service import WeatherService
from utils.logger import get_logger
from utils.checkpoint_manager import find_latest_checkpoint, list_checkpoints, get_checkpoint_info
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
    agent_type: str = Query("sac", description="Agent type: sac (recommended), ppo, or bandit"),
    include_weather: bool = Query(True, description="Include weather impact analysis")
) -> PriceRecommendation:
    """
    Get AI-powered price recommendation for a product.
    
    Uses trained RL agents to recommend optimal prices based on:
    - Current market conditions
    - Inventory levels
    - Demand patterns
    - Weather impact
    
    **Agent Selection:**
    - **sac** (default): Best performance (156.29 reward) - recommended for production
    - **ppo**: Alternative model (153.97 reward) - use for A/B testing
    - **bandit**: Fallback only (0.897 reward) - use if SAC/PPO unavailable
    
    Args:
        product_id: The product identifier
        agent_type: Type of agent to use (sac, ppo, or bandit) - defaults to sac
        include_weather: Include weather impact in response (default: true)
    
    Returns:
        PriceRecommendation with confidence score and explanation factors
    """
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 PRICE RECOMMENDATION REQUEST: product_id={product_id}, agent={agent_type}")
        logger.info(f"{'='*80}")
        
        # Validate agent type
        if agent_type not in ["ppo", "sac", "bandit"]:
            logger.error(f"❌ Invalid agent_type: {agent_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent_type. Must be one of: sac (recommended), ppo, or bandit"
            )
        
        # Log agent selection
        if agent_type == "sac":
            logger.info(f"✅ [RECOMMENDED] Using SAC agent for {product_id}")
        else:
            logger.warning(f"⚠️  Using {agent_type} agent (not recommended - SAC preferred)")
        
        # Find latest trained checkpoint for agent type
        logger.info(f"🔎 Searching for latest {agent_type.upper()} checkpoint...")
        checkpoint_path = find_latest_checkpoint(agent_type)
        if checkpoint_path:
            logger.info(f"✅ Found checkpoint: {checkpoint_path}")
        else:
            logger.warning(f"❌ No trained checkpoint found for {agent_type}, will try untrained agent")
        
        # Initialize pricing service with specified agent and checkpoint
        logger.info(f"⚙️  Initializing PricingService with {agent_type} agent...")
        service = PricingService(agent_type=agent_type, checkpoint_path=checkpoint_path)
        
        if not service.agent:
            logger.error(f"❌ PricingService failed to initialize agent - returning error")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize {agent_type} agent. Check backend logs."
            )
        
        logger.info(f"✅ PricingService initialized successfully")
        
        # Get recommendation
        logger.info(f"🤖 Requesting recommendation from agent...")
        recommendation = service.get_recommendation(product_id)
        
        if not recommendation:
            logger.error(f"❌ Agent returned None for {product_id}")
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
        
        logger.info(f"✅ SUCCESS: Recommendation for {product_id}")
        logger.info(f"  Current Price: ${recommendation['current_price']:.2f}")
        logger.info(f"  Recommended Price: ${recommendation['recommended_price']:.2f}")
        logger.info(f"  Confidence: {recommendation['confidence']:.0%}")
        logger.info(f"{'='*80}\n")
        
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
        logger.error(f"❌ ERROR getting price recommendation: {e}", exc_info=True)
        logger.info(f"{'='*80}\n")
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


@router.get("/checkpoints/list", response_model=dict)
async def list_available_checkpoints() -> dict:
    """
    List all available trained agent checkpoints.
    
    Returns information about all trained models organized by agent type,
    including filenames, reward scores, and modification times.
    """
    try:
        checkpoints = list_checkpoints()
        
        formatted_response = {}
        for agent_type, checkpoints_list in checkpoints.items():
            formatted_response[agent_type] = [
                {
                    "filename": cp["filename"],
                    "reward_score": get_checkpoint_info(cp["path"]).get("reward_score") 
                        if get_checkpoint_info(cp["path"]) else None,
                    "modified_timestamp": cp["modified"]
                }
                for cp in checkpoints_list
            ]
        
        logger.info(f"Listed {sum(len(v) for v in formatted_response.values())} checkpoints")
        return {
            "checkpoints": formatted_response,
            "total_count": sum(len(v) for v in checkpoints.values())
        }
        
    except Exception as e:
        logger.error(f"Error listing checkpoints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkpoints/latest/{agent_type}", response_model=dict)
async def get_latest_checkpoint(agent_type: str) -> dict:
    """
    Get the latest trained checkpoint for a specific agent type.
    
    - **agent_type**: Agent type (ppo, sac, bandit)
    """
    try:
        if agent_type not in ["ppo", "sac", "bandit"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent_type. Must be one of: ppo, sac, bandit"
            )
        
        checkpoint_path = find_latest_checkpoint(agent_type)
        
        if not checkpoint_path:
            raise HTTPException(
                status_code=404,
                detail=f"No checkpoint found for agent type: {agent_type}"
            )
        
        checkpoint_info = get_checkpoint_info(checkpoint_path)
        
        return {
            "agent_type": agent_type,
            "filename": Path(checkpoint_path).name,
            "path": checkpoint_path,
            "reward_score": checkpoint_info.get("reward_score") if checkpoint_info else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest checkpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
