"""Dashboard and metrics endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from services.inventory_service import InventoryService
from services.pricing_service import PricingService
from utils.logger import get_logger
from models import get_session, Transaction, Product, PriceHistory, AgentMetrics

logger = get_logger(__name__)
router = APIRouter(prefix="/api/metrics", tags=["metrics"])


class DashboardMetric(BaseModel):
    """Single dashboard metric."""
    label: str
    value: float
    unit: str
    trend: Optional[str] = None  # "up", "down", "stable"
    change_pct: Optional[float] = None


class DashboardSummary(BaseModel):
    """Dashboard summary with key metrics."""
    total_revenue: float
    revenue_trend: str
    total_transactions: int
    average_order_value: float
    
    inventory_health: float
    items_low_stock: int
    items_critical: int
    
    avg_price_change: float
    pricing_confidence: float
    
    last_updated: str


class RecommendationMetrics(BaseModel):
    """Price recommendation effectiveness metrics."""
    total_recommendations: int
    recommendations_applied: int
    applied_rate: float
    avg_confidence: float
    avg_revenue_impact: float


class PricingOpportunity(BaseModel):
    """Pricing optimization opportunity."""
    product_id: str
    product_name: str
    current_price: float
    recommended_price: float
    potential_impact: str  # "increase_revenue", "improve_margin", "increase_sales"
    expected_change: float  # percentage
    confidence: float


class PerformanceMetrics(BaseModel):
    """Overall system performance metrics."""
    uptime_pct: float
    avg_recommendation_latency_ms: float
    successful_predictions: int
    failed_predictions: int
    accuracy: float
    last_training_date: Optional[str] = None


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    days: int = Query(30, ge=1, le=365, description="Days of history to include")
) -> DashboardSummary:
    """
    Get comprehensive dashboard summary.
    
    - **days**: Number of days of history to include
    
    Returns key metrics for monitoring system performance.
    """
    try:
        session = get_session()
        inventory_service = InventoryService()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Revenue metrics
        transactions = session.query(Transaction).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).all()
        
        total_revenue = sum(t.total for t in transactions) if transactions else 0
        total_transactions = len(transactions)
        avg_order_value = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Revenue trend (compare to previous period)
        prev_start = start_date - timedelta(days=days)
        prev_transactions = session.query(Transaction).filter(
            Transaction.created_at >= prev_start,
            Transaction.created_at < start_date
        ).all()
        prev_revenue = sum(t.total for t in prev_transactions) if prev_transactions else 1
        revenue_change_pct = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0
        revenue_trend = "up" if revenue_change_pct > 0 else "down" if revenue_change_pct < 0 else "stable"
        
        # Inventory metrics
        inv_metrics = inventory_service.get_inventory_metrics()
        inventory_health = inv_metrics.get("health_score", 0.0)
        items_low_stock = inv_metrics.get("items_low_stock", 0)
        items_critical = inv_metrics.get("items_critical", 0)
        
        # Pricing metrics
        price_changes = session.query(PriceHistory).filter(
            PriceHistory.created_at >= start_date
        ).all()
        
        avg_price_change = 0.0
        if price_changes:
            changes = []
            for ph in price_changes:
                if ph.old_price and ph.old_price > 0:
                    change = ((ph.new_price - ph.old_price) / ph.old_price)
                    changes.append(abs(change))
            if changes:
                avg_price_change = sum(changes) / len(changes)
        
        # Recommendation confidence (from agent metrics)
        agent_metrics = session.query(AgentMetrics).filter(
            AgentMetrics.created_at >= start_date
        ).all()
        
        pricing_confidence = 0.0
        if agent_metrics:
            confidences = [m.confidence for m in agent_metrics if m.confidence]
            if confidences:
                pricing_confidence = sum(confidences) / len(confidences)
        
        session.close()
        
        logger.info("Dashboard summary retrieved")
        return DashboardSummary(
            total_revenue=total_revenue,
            revenue_trend=revenue_trend,
            total_transactions=total_transactions,
            average_order_value=avg_order_value,
            inventory_health=inventory_health,
            items_low_stock=items_low_stock,
            items_critical=items_critical,
            avg_price_change=avg_price_change * 100,
            pricing_confidence=pricing_confidence,
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", response_model=RecommendationMetrics)
async def get_recommendation_metrics(
    days: int = Query(30, ge=1, le=365, description="Days to analyze")
) -> RecommendationMetrics:
    """
    Get metrics on pricing recommendation effectiveness.
    
    - **days**: Number of days to include in analysis
    
    Tracks how often recommendations are applied and their impact.
    """
    try:
        session = get_session()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get agent metrics
        agent_metrics = session.query(AgentMetrics).filter(
            AgentMetrics.created_at >= start_date
        ).all()
        
        total_recommendations = len(agent_metrics)
        recommendations_applied = len([m for m in agent_metrics if m.applied])
        applied_rate = (recommendations_applied / total_recommendations * 100) if total_recommendations > 0 else 0
        
        # Average confidence
        avg_confidence = 0.0
        if agent_metrics:
            confidences = [m.confidence for m in agent_metrics if m.confidence]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
        
        # Calculate revenue impact
        avg_revenue_impact = 0.0
        impacts = [m.revenue_impact for m in agent_metrics if m.revenue_impact]
        if impacts:
            avg_revenue_impact = sum(impacts) / len(impacts)
        
        session.close()
        
        logger.info("Recommendation metrics retrieved")
        return RecommendationMetrics(
            total_recommendations=total_recommendations,
            recommendations_applied=recommendations_applied,
            applied_rate=applied_rate,
            avg_confidence=avg_confidence,
            avg_revenue_impact=avg_revenue_impact
        )
        
    except Exception as e:
        logger.error(f"Error getting recommendation metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities", response_model=List[PricingOpportunity])
async def get_pricing_opportunities(
    limit: int = Query(10, ge=1, le=50, description="Maximum opportunities to return")
) -> List[PricingOpportunity]:
    """
    Get top pricing optimization opportunities.
    
    - **limit**: Maximum number of opportunities to return
    
    Identifies products where pricing adjustments could improve revenue/margin.
    """
    try:
        session = get_session()
        pricing_service = PricingService(agent_type="ppo")
        inventory_service = InventoryService()
        
        products = session.query(Product).all()
        opportunities = []
        
        for product in products:
            try:
                # Get recommendation
                rec = pricing_service.get_recommendation(product.id)
                if not rec:
                    continue
                
                current_price = rec["current_price"]
                recommended_price = rec["recommended_price"]
                
                # Calculate potential impact
                if recommended_price != current_price:
                    change_pct = ((recommended_price - current_price) / current_price * 100)
                    
                    # Determine impact type
                    if change_pct > 5:
                        impact_type = "increase_revenue"
                    elif change_pct < -5:
                        impact_type = "increase_sales"
                    else:
                        impact_type = "improve_margin"
                    
                    opportunities.append(PricingOpportunity(
                        product_id=product.id,
                        product_name=product.name,
                        current_price=current_price,
                        recommended_price=recommended_price,
                        potential_impact=impact_type,
                        expected_change=change_pct,
                        confidence=rec["confidence"]
                    ))
            except Exception as e:
                logger.warning(f"Could not get recommendation for {product.id}: {e}")
                continue
        
        # Sort by confidence and potential impact
        opportunities.sort(key=lambda x: x.confidence * abs(x.expected_change), reverse=True)
        
        session.close()
        logger.info(f"Found {len(opportunities)} pricing opportunities")
        
        return opportunities[:limit]
        
    except Exception as e:
        logger.error(f"Error getting pricing opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics() -> PerformanceMetrics:
    """
    Get overall system performance metrics.
    
    Includes prediction accuracy, latency, and training status.
    """
    try:
        session = get_session()
        
        # Get all agent metrics
        agent_metrics = session.query(AgentMetrics).all()
        
        successful = len([m for m in agent_metrics if m.reward and m.reward > 0])
        failed = len([m for m in agent_metrics if m.reward and m.reward <= 0])
        total = len(agent_metrics)
        
        accuracy = (successful / total * 100) if total > 0 else 0
        
        # Get latest training date
        last_training = None
        if agent_metrics:
            latest = max(agent_metrics, key=lambda x: x.created_at)
            last_training = latest.created_at.isoformat()
        
        session.close()
        
        logger.info("Performance metrics retrieved")
        return PerformanceMetrics(
            uptime_pct=99.9,  # Placeholder
            avg_recommendation_latency_ms=150,  # Placeholder
            successful_predictions=successful,
            failed_predictions=failed,
            accuracy=accuracy,
            last_training_date=last_training
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))