"""Inventory management endpoints."""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from services.inventory_service import InventoryService
from utils.logger import get_logger
from models import get_session, InventoryItem as DBInventoryItem, Product

logger = get_logger(__name__)
router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class InventoryItem(BaseModel):
    """Inventory item schema."""
    product_id: str
    product_name: str
    current_stock: int
    reorder_point: int
    status: str
    days_to_stockout: Optional[float] = None


class ReorderAlert(BaseModel):
    """Reorder alert."""
    product_id: str
    product_name: str
    current_stock: int
    reorder_point: int
    days_to_stockout: float
    urgency: str  # "critical", "warning", "info"


class InventoryMetrics(BaseModel):
    """Overall inventory metrics."""
    total_items: int
    total_units: int
    total_value: float
    items_low_stock: int
    items_critical: int
    health_score: float
    average_turnover: float


class StockUpdateRequest(BaseModel):
    """Request to update stock."""
    quantity_change: int
    reason: str = "adjustment"


@router.get("/items", response_model=List[InventoryItem])
async def list_inventory() -> List[InventoryItem]:
    """
    Get all inventory items with current stock levels and status.
    
    Returns items with indicators for low stock, reorder alerts, etc.
    """
    try:
        inventory_service = InventoryService()
        session = get_session()
        
        # Get all products
        products = session.query(Product).all()
        session.close()
        
        items = []
        for product in products:
            inv_data = inventory_service.get_inventory(product.id)
            if inv_data:
                items.append(InventoryItem(
                    product_id=product.id,
                    product_name=product.name,
                    current_stock=inv_data["current_stock"],
                    reorder_point=inv_data["reorder_point"],
                    status=inv_data["status"],
                    days_to_stockout=inv_data.get("days_to_stockout")
                ))
        
        logger.info(f"Retrieved {len(items)} inventory items")
        return items
        
    except Exception as e:
        logger.error(f"Error listing inventory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{product_id}", response_model=InventoryItem)
async def get_inventory_item(product_id: str) -> InventoryItem:
    """
    Get inventory level for a specific product.
    
    - **product_id**: The product identifier
    
    Returns current stock, reorder point, and status indicators.
    """
    try:
        inventory_service = InventoryService()
        session = get_session()
        
        product = session.query(Product).filter(Product.id == product_id).first()
        session.close()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        inv_data = inventory_service.get_inventory(product_id)
        if not inv_data:
            raise HTTPException(status_code=500, detail="Could not retrieve inventory data")
        
        logger.info(f"Retrieved inventory for {product_id}")
        return InventoryItem(
            product_id=product.id,
            product_name=product.name,
            current_stock=inv_data["current_stock"],
            reorder_point=inv_data["reorder_point"],
            status=inv_data["status"],
            days_to_stockout=inv_data.get("days_to_stockout")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inventory item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/items/{product_id}", response_model=dict)
async def update_inventory(
    product_id: str,
    request: StockUpdateRequest
) -> dict:
    """
    Update inventory level for a product.
    
    - **product_id**: The product identifier
    - **request**: Contains quantity change and reason
    
    Records the stock adjustment and checks for reorder alerts.
    """
    try:
        logger.info(f"Updating inventory for {product_id}: {request.quantity_change} ({request.reason})")
        
        inventory_service = InventoryService()
        session = get_session()
        
        # Verify product exists
        product = session.query(Product).filter(Product.id == product_id).first()
        session.close()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Update stock
        result = inventory_service.update_stock(
            product_id,
            request.quantity_change,
            request.reason
        )
        
        # Get updated inventory
        updated_inv = inventory_service.get_inventory(product_id)
        
        logger.info(f"Inventory updated for {product_id}")
        return {
            "success": True,
            "product_id": product_id,
            "quantity_change": request.quantity_change,
            "new_stock": updated_inv["current_stock"],
            "status": updated_inv["status"],
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating inventory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[ReorderAlert])
async def get_reorder_alerts(
    urgency: str = Query("all", description="Filter by urgency: critical, warning, info, or all")
) -> List[ReorderAlert]:
    """
    Get items that need reordering.
    
    - **urgency**: Filter alerts by urgency level
    
    Returns items below reorder point with estimated days to stockout.
    """
    try:
        inventory_service = InventoryService()
        alerts_data = inventory_service.check_reorder_alerts()
        
        if not alerts_data:
            return []
        
        session = get_session()
        alerts = []
        
        for alert in alerts_data:
            # Determine urgency
            days_to_stockout = alert.get("days_to_stockout", 999)
            if days_to_stockout <= 3:
                alert_urgency = "critical"
            elif days_to_stockout <= 7:
                alert_urgency = "warning"
            else:
                alert_urgency = "info"
            
            # Filter by urgency
            if urgency != "all" and alert_urgency != urgency:
                continue
            
            product = session.query(Product).filter(Product.id == alert["product_id"]).first()
            if product:
                alerts.append(ReorderAlert(
                    product_id=alert["product_id"],
                    product_name=product.name,
                    current_stock=alert["current_stock"],
                    reorder_point=alert["reorder_point"],
                    days_to_stockout=alert["days_to_stockout"],
                    urgency=alert_urgency
                ))
        
        session.close()
        logger.info(f"Retrieved {len(alerts)} reorder alerts")
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting reorder alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=InventoryMetrics)
async def get_inventory_metrics() -> InventoryMetrics:
    """
    Get overall inventory metrics and health score.
    
    Returns aggregate statistics on stock levels, turnover, and health.
    """
    try:
        inventory_service = InventoryService()
        metrics = inventory_service.get_inventory_metrics()
        
        logger.info("Retrieved inventory metrics")
        return InventoryMetrics(
            total_items=metrics.get("total_items", 0),
            total_units=metrics.get("total_units", 0),
            total_value=metrics.get("total_value", 0.0),
            items_low_stock=metrics.get("items_low_stock", 0),
            items_critical=metrics.get("items_critical", 0),
            health_score=metrics.get("health_score", 0.0),
            average_turnover=metrics.get("average_turnover", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Error getting inventory metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
