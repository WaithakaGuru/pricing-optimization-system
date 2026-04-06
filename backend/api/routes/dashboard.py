"""Dashboard and metrics endpoints."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
from services.inventory_service import InventoryService
from services.pricing_service import PricingService
from utils.logger import get_logger
from models import get_session, Transaction, Product, PriceHistory, AgentMetrics

logger = get_logger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


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


@router.get("", response_model=DashboardSummary)
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
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Revenue metrics
        transactions = session.query(Transaction).filter(
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        ).all()
        
        total_revenue = sum(t.total for t in transactions) if transactions else 0
        total_transactions = len(transactions)
        avg_order_value = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Revenue trend (compare to previous period)
        prev_start = start_date - timedelta(days=days)
        prev_transactions = session.query(Transaction).filter(
            Transaction.timestamp >= prev_start,
            Transaction.timestamp < start_date
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
            PriceHistory.timestamp >= start_date
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
            AgentMetrics.timestamp >= start_date
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
            last_updated=datetime.now().isoformat()
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
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get agent metrics
        agent_metrics = session.query(AgentMetrics).filter(
            AgentMetrics.timestamp >= start_date
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
            latest = max(agent_metrics, key=lambda x: x.timestamp)
            last_training = latest.timestamp.isoformat()
        
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


# ============================================================================
# MODEL COMPARISON AND EVALUATION ENDPOINTS
# ============================================================================

import json
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent.parent
EVAL_REPORT_PATH = BACKEND_DIR / "eval_report.json"
REPORTS_DIR = BACKEND_DIR / "reports"


def _load_eval_report() -> Optional[dict]:
    """Load evaluation report from disk."""
    if EVAL_REPORT_PATH.exists():
        try:
            with open(EVAL_REPORT_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load eval report: {e}")
    return None


@router.get("/models")
async def get_models_dashboard() -> dict:
    """
    Get comprehensive model dashboard with all agent comparisons and metrics.
    
    Returns comprehensive evaluation data including:
    - Agent rankings and performance metrics
    - Training history and improvements
    - Confidence levels and recommendations
    - Deployment guidance
    
    Returns:
        {
            "status": "ready",
            "timestamp": "2026-03-27T05:40:00",
            "summary": {
                "best_agent": "sac",
                "best_reward": 156.29,
                "agents_trained": 3,
                "total_episodes": 1500
            },
            "agents": {
                "sac": {...metrics...},
                "ppo": {...metrics...},
                "bandit": {...metrics...}
            },
            "recommendations": {...}
        }
    """
    try:
        eval_report = _load_eval_report()
        
        if not eval_report:
            return {
                "status": "no_evaluation",
                "message": "Run eval_all_agents.py to generate evaluation report",
                "next_steps": [
                    "Train all models with train_all_models.py",
                    "Generate evaluation report with eval_all_agents.py",
                    "Check back for comprehensive dashboard"
                ]
            }
        
        logger.info("Models dashboard retrieved")
        return eval_report
        
    except Exception as e:
        logger.error(f"Error getting models dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/summary")
async def get_models_summary() -> dict:
    """
    Get quick summary of model performance for dashboard cards.
    
    Returns quick performance metrics for each agent with status indicators.
    """
    try:
        eval_report = _load_eval_report()
        
        if not eval_report:
            raise HTTPException(
                status_code=404,
                detail="Evaluation report not found. Run eval_all_agents.py first."
            )
        
        best_agent = eval_report.get("best_agent")
        agent_comparison = eval_report.get("agent_comparison", {})
        
        # Build summary for each agent
        agents_summary = {}
        for agent_type, metrics in agent_comparison.items():
            mean_reward = metrics.get("mean_reward", 0)
            
            # Assign status based on performance
            if agent_type == best_agent:
                status = "recommended"
                color = "green"
            elif mean_reward > 50:
                status = "acceptable"
                color = "blue"
            else:
                status = "fallback"
                color = "orange"
            
            agents_summary[agent_type] = {
                "reward": mean_reward,
                "std": metrics.get("std_reward", 0),
                "status": status,
                "color": color,
                "confidence": metrics.get("confidence", "unknown")
            }
        
        logger.info("Models summary retrieved")
        return {
            "best_agent": best_agent,
            "best_reward": agent_comparison.get(best_agent, {}).get("mean_reward", 0),
            "agents": agents_summary,
            "last_updated": eval_report.get("timestamp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting models summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/comparison")
async def get_models_comparison() -> dict:
    """Get detailed model comparison for analysis views."""
    try:
        eval_report = _load_eval_report()
        
        if not eval_report:
            raise HTTPException(status_code=404, detail="Evaluation report not found.")
        
        agent_comparison = eval_report.get("agent_comparison", {})
        
        # Enrich with qualitative analysis
        qualitative_data = {
            "sac": {
                "type": "Soft Actor-Critic (Off-Policy)",
                "strengths": [
                    "Highest reward (156.29)",
                    "Stable learning with entropy regularization",
                    "Explores via temperature scaling",
                    "Production-ready performance"
                ],
                "weaknesses": [
                    "Requires more computational resources",
                    "More hyperparameters to tune"
                ],
                "best_for": "Production pricing, complex decision spaces"
            },
            "ppo": {
                "type": "Proximal Policy Optimization (On-Policy)",
                "strengths": [
                    "Strong performance (153.97 reward, 1.5% below SAC)",
                    "Stable, reliable training",
                    "Good for A/B testing",
                    "Lower variance updates"
                ],
                "weaknesses": [
                    "Slightly lower reward than SAC",
                    "Less sample efficient than SAC"
                ],
                "best_for": "A/B testing, conservative adoption"
            },
            "bandit": {
                "type": "Contextual Multi-Armed Bandit",
                "strengths": [
                    "Ultra-fast decisions (stateless)",
                    "Simple, interpretable logic",
                    "Good exploration-exploitation tradeoff"
                ],
                "weaknesses": [
                    "Lowest reward (0.897)",
                    "No true learning across episodes",
                    "Limited context awareness"
                ],
                "best_for": "Fallback only, emergency pricing"
            }
        }
        
        comparison = {}
        for agent_type, metrics in agent_comparison.items():
            qual = qualitative_data.get(agent_type, {})
            comparison[agent_type] = {
                **metrics,
                "type": qual.get("type"),
                "strengths": qual.get("strengths", []),
                "weaknesses": qual.get("weaknesses", []),
                "best_for": qual.get("best_for", "")
            }
        
        logger.info("Models comparison retrieved")
        return {
            "agents": comparison,
            "timestamp": eval_report.get("timestamp"),
            "recommendation": f"Deploy {eval_report.get('best_agent', 'sac').upper()} for production"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting models comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/recommendations")
async def get_deployment_recommendations() -> dict:
    """Get deployment recommendations and next steps."""
    try:
        eval_report = _load_eval_report()
        
        if not eval_report:
            raise HTTPException(status_code=404, detail="Evaluation report not found.")
        
        best_agent = eval_report.get("best_agent", "sac")
        agent_comparison = eval_report.get("agent_comparison", {})
        agents_ranked = sorted(
            agent_comparison.items(),
            key=lambda x: x[1].get("mean_reward", 0),
            reverse=True
        )
        
        logger.info("Deployment recommendations retrieved")
        return {
            "deployment": {
                "primary": agents_ranked[0][0] if agents_ranked else best_agent,
                "fallback": agents_ranked[1][0] if len(agents_ranked) > 1 else "ppo",
                "emergency": agents_ranked[2][0] if len(agents_ranked) > 2 else "bandit"
            },
            "actions": [
                {
                    "priority": "high",
                    "action": f"Deploy {agents_ranked[0][0].upper()}",
                    "reason": f"Best performance ({agents_ranked[0][1].get('mean_reward', 0):.2f} reward)"
                },
                {
                    "priority": "medium",
                    "action": "Set up A/B testing with secondary agent",
                    "reason": "Validate performance in production environment"
                },
                {
                    "priority": "medium",
                    "action": "Configure fallback chain",
                    "reason": "Ensure graceful degradation if primary fails"
                },
                {
                    "priority": "low",
                    "action": "Schedule monthly retraining",
                    "reason": "Keep models updated with new data"
                }
            ],
            "monitoring": [
                "Track actual price acceptance rate vs recommendations",
                "Monitor reward drift (compare predicted vs actual revenue)",
                "Check for inventory imbalances correlated with pricing",
                "Alert if agent success rate drops below 90%",
                "Weekly review of anomalies in price recommendations"
            ],
            "success_metrics": {
                "primary": "Revenue increase > 5% vs baseline",
                "secondary": "Price acceptance rate > 85%",
                "tertiary": "Inventory turnover improvement > 3%"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def dashboard_health() -> dict:
    """Get dashboard health status."""
    try:
        components = {
            "evaluation_report": EVAL_REPORT_PATH.exists(),
            "visualizations": REPORTS_DIR.exists() and bool(list(REPORTS_DIR.glob("*.png"))),
            "checkpoints": (BACKEND_DIR / "models" / "rl_checkpoints").exists(),
            "api_server": True
        }
        
        overall = "healthy" if all(components.values()) else "degraded"
        
        logger.info(f"Dashboard health: {overall}")
        return {
            "overall": overall,
            "timestamp": datetime.now().isoformat(),
            "components": components
        }
        
    except Exception as e:
        logger.error(f"Error checking dashboard health: {e}")
        return {
            "overall": "unhealthy",
            "error": str(e)
        }


@router.get("/visualizations")
async def list_visualizations() -> dict:
    """
    List all available visualization charts.
    
    Returns:
        {
            "charts": [
                {
                    "filename": "01_reward_comparison.png",
                    "title": "Agent Reward Comparison",
                    "description": "Bar chart comparing mean rewards across agents",
                    "url": "/api/dashboard/visualizations/01_reward_comparison.png"
                },
                ...
            ]
        }
    """
    try:
        if not REPORTS_DIR.exists():
            return {"charts": [], "message": "No visualizations available yet"}
        
        chart_info = {
            "01_reward_comparison.png": {
                "title": "Agent Reward Comparison",
                "description": "Mean rewards with error bars for each agent"
            },
            "02_efficiency_scatter.png": {
                "title": "Training Efficiency",
                "description": "Training time vs reward achieved (Pareto frontier)"
            },
            "03_characteristics_radar.png": {
                "title": "Agent Characteristics",
                "description": "Multi-dimensional comparison (speed, stability, sample efficiency, etc.)"
            },
            "04_recommendation_card.png": {
                "title": "Deployment Recommendation",
                "description": "Summary card with recommended agent and next steps"
            }
        }
        
        charts = []
        for filename, info in chart_info.items():
            filepath = REPORTS_DIR / filename
            if filepath.exists():
                charts.append({
                    "filename": filename,
                    "title": info["title"],
                    "description": info["description"],
                    "url": f"/api/dashboard/visualizations/{filename}",
                    "size_kb": filepath.stat().st_size / 1024
                })
        
        logger.info(f"Listed {len(charts)} visualizations")
        return {"charts": charts}
        
    except Exception as e:
        logger.error(f"Error listing visualizations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualizations/{filename}")
async def get_visualization(filename: str) -> FileResponse:
    """
    Serve visualization PNG files.
    
    - **filename**: Name of the chart file (e.g., "01_reward_comparison.png")
    
    Returns the PNG image file with appropriate headers.
    """
    try:
        # Validate filename to prevent directory traversal
        allowed_files = {
            "01_reward_comparison.png",
            "02_efficiency_scatter.png",
            "03_characteristics_radar.png",
            "04_recommendation_card.png"
        }
        
        if filename not in allowed_files:
            raise HTTPException(status_code=404, detail=f"Chart not found: {filename}")
        
        filepath = REPORTS_DIR / filename
        
        if not filepath.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Visualization not generated yet: {filename}. Run eval_all_agents.py to generate."
            )
        
        if not filepath.is_file():
            raise HTTPException(status_code=400, detail=f"Invalid file: {filename}")
        
        logger.info(f"Serving visualization: {filename}")
        return FileResponse(
            filepath,
            media_type="image/png",
            filename=filename,
            headers={"Cache-Control": "public, max-age=3600"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving visualization {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving visualization: {str(e)}")