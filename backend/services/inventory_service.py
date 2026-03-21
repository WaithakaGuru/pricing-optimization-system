"""Inventory service - real stock management with database integration."""
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import Session
from typing import Optional, Dict, List

from models import InventoryItem, Transaction, Product

logger = logging.getLogger(__name__)


class InventoryService:
    """
    Service for inventory management with real database integration.
    
    Tracks:
    - Stock levels and movements
    - Turnover rates (demand velocity)
    - Reorder points and alerts
    - Inventory health metrics for RL state
    """

    def __init__(self, db_url: str = "sqlite:///pricing.db"):
        """Initialize inventory service with database connection."""
        self.engine = create_engine(db_url)
        logger.info(f"InventoryService initialized with {db_url}")

    def get_inventory(self, product_id: str) -> Optional[Dict]:
        """
        Get current inventory level for a product.
        
        Returns:
            {
                "product_id": "PROD-001",
                "current_stock": 150,
                "reorder_point": 50,
                "last_restock": "2024-03-19",
                "status": "healthy"  # or "low", "critical"
            }
        """
        try:
            with Session(self.engine) as session:
                inv = session.query(InventoryItem).filter(
                    InventoryItem.product_id == product_id
                ).first()
                
                if not inv:
                    logger.warning(f"Inventory not found for {product_id}")
                    return None
                
                status = "critical" if inv.quantity < inv.reorder_point * 0.5 else \
                        "low" if inv.quantity < inv.reorder_point else "healthy"
                
                return {
                    "product_id": product_id,
                    "current_stock": inv.quantity,
                    "reorder_point": inv.reorder_point,
                    "last_restock": inv.last_restock_date.isoformat() if inv.last_restock_date else None,
                    "status": status,
                    "warehouse_location": inv.warehouse_location,
                }
        except Exception as e:
            logger.error(f"Error fetching inventory: {e}")
            return None

    def update_stock(
        self,
        product_id: str,
        quantity_change: int,
        reason: str = "sale"
    ) -> Optional[Dict]:
        """
        Update stock level after sale or restock.
        
        Args:
            product_id: Product identifier
            quantity_change: Change amount (negative for sale, positive for restock)
            reason: "sale", "restock", "adjustment", "damage"
            
        Returns:
            Updated inventory dict or None if failed
        """
        try:
            with Session(self.engine) as session:
                inv = session.query(InventoryItem).filter(
                    InventoryItem.product_id == product_id
                ).first()
                
                if not inv:
                    logger.error(f"Inventory not found: {product_id}")
                    return None
                
                old_qty = inv.quantity
                inv.quantity += quantity_change
                inv.updated_at = datetime.now()
                
                # Update last restock if restocking
                if quantity_change > 0:
                    inv.last_restock_date = datetime.now()
                
                session.commit()
                
                # Build response without opening a new session
                status = "critical" if inv.quantity < inv.reorder_point * 0.5 else \
                        "low" if inv.quantity < inv.reorder_point else "healthy"
                
                logger.info(
                    f"Stock updated: {product_id} "
                    f"{old_qty} → {inv.quantity} (reason: {reason})"
                )
                
                return {
                    "product_id": product_id,
                    "current_stock": inv.quantity,
                    "reorder_point": inv.reorder_point,
                    "last_restock": inv.last_restock_date.isoformat() if inv.last_restock_date else None,
                    "status": status,
                    "warehouse_location": inv.warehouse_location,
                }
                
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
            return None

    def get_turnover_rate(self, product_id: str, days: int = 30) -> Optional[float]:
        """
        Get inventory turnover rate (units sold / avg inventory).
        
        Used by StateBuilder for demand signal.
        
        Args:
            product_id: Product identifier
            days: Look-back period (days)
            
        Returns:
            Turnover rate (lower = slower, higher = faster)
        """
        try:
            with Session(self.engine) as session:
                # Total sold in period
                cutoff_date = datetime.now() - timedelta(days=days)
                sold = session.query(func.sum(Transaction.quantity)).filter(
                    and_(
                        Transaction.product_id == product_id,
                        Transaction.timestamp >= cutoff_date,
                    )
                ).scalar() or 0
                
                # Average inventory in period
                inv = session.query(InventoryItem).filter(
                    InventoryItem.product_id == product_id
                ).first()
                
                if not inv or inv.quantity == 0:
                    return 0.0
                
                turnover = sold / (inv.quantity * days)
                logger.debug(f"Turnover for {product_id}: {turnover:.4f}")
                
                return turnover
                
        except Exception as e:
            logger.error(f"Error calculating turnover: {e}")
            return 0.0

    def check_reorder_alerts(self) -> List[Dict]:
        """
        Check for items below reorder point.
        
        Returns:
            List of alert dicts for products needing restock
            [
                {
                    "product_id": "PROD-001",
                    "current": 45,
                    "reorder_point": 50,
                    "days_to_stockout": 8.5
                },
                ...
            ]
        """
        try:
            with Session(self.engine) as session:
                low_stock = session.query(InventoryItem).filter(
                    InventoryItem.quantity < InventoryItem.reorder_point
                ).all()
                
                alerts = []
                for inv in low_stock:
                    turnover = self.get_turnover_rate(inv.product_id, days=7)
                    
                    if turnover > 0:
                        days_to_out = inv.quantity / turnover
                    else:
                        days_to_out = float('inf')
                    
                    alerts.append({
                        "product_id": inv.product_id,
                        "current": inv.quantity,
                        "reorder_point": inv.reorder_point,
                        "days_to_stockout": days_to_out,
                    })
                
                if alerts:
                    logger.warning(f"Reorder alerts: {len(alerts)} items")
                
                return alerts
                
        except Exception as e:
            logger.error(f"Error checking reorder alerts: {e}")
            return []

    def get_inventory_metrics(self) -> Dict:
        """
        Get overall inventory health metrics.
        
        Returns:
            {
                "total_items": 50,
                "total_units": 5000,
                "items_low_stock": 3,
                "avg_turnover": 0.15,
                "total_value": 50000.00,
                "health_score": 0.85
            }
        """
        try:
            with Session(self.engine) as session:
                inventories = session.query(InventoryItem).all()
                
                total_items = len(inventories)
                total_units = sum(inv.quantity for inv in inventories)
                
                low_stock = sum(
                    1 for inv in inventories
                    if inv.quantity < inv.reorder_point
                )
                
                total_value = 0.0
                avg_turnover = 0.0
                
                for inv in inventories:
                    # Get product for price
                    product = session.query(Product).filter(
                        Product.product_id == inv.product_id
                    ).first()
                    
                    if product:
                        total_value += inv.quantity * product.base_price
                        turnover = self.get_turnover_rate(inv.product_id, days=30)
                        avg_turnover += turnover
                
                avg_turnover = avg_turnover / total_items if total_items > 0 else 0
                
                # Health score: 1.0 if all healthy, scales down with low stock
                health_score = 1.0 - (low_stock / total_items * 0.5) if total_items > 0 else 0
                
                return {
                    "total_items": total_items,
                    "total_units": total_units,
                    "items_low_stock": low_stock,
                    "avg_turnover": avg_turnover,
                    "total_value": total_value,
                    "health_score": health_score,
                }
                
        except Exception as e:
            logger.error(f"Error getting inventory metrics: {e}")
            return {}

    def get_inventory_for_state(self, product_id: str) -> Dict:
        """
        Get inventory data formatted for RL agent state space.
        
        Returns:
            Normalized inventory features
            {
                "inventory_level": 0.5,      # normalized [0, 1]
                "turnover_rate": 0.15,       # sales per day
                "days_to_stockout": 30.0,    # estimated
                "reorder_status": 0.8,       # ratio of current to reorder point
            }
        """
        inv_dict = self.get_inventory(product_id)
        
        if not inv_dict:
            logger.warning(f"Using default inventory for {product_id}")
            return {
                "inventory_level": 0.5,
                "turnover_rate": 0.1,
                "days_to_stockout": 100.0,
                "reorder_status": 1.0,
            }
        
        current = inv_dict["current_stock"]
        reorder = inv_dict["reorder_point"]
        turnover = self.get_turnover_rate(product_id, days=7)
        
        # Normalize inventory: [0, 2*reorder] → [0, 1]
        inv_norm = min(current / (reorder * 2), 1.0)
        
        # Days to stockout
        days_to_out = current / turnover if turnover > 0 else 1000.0
        
        # Reorder status: ratio to reorder point
        reorder_status = current / reorder if reorder > 0 else 1.0
        
        return {
            "inventory_level": inv_norm,
            "turnover_rate": turnover,
            "days_to_stockout": days_to_out,
            "reorder_status": reorder_status,
        }
