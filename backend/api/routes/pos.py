"""POS transaction endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4
from services.pricing_service import PricingService
from services.inventory_service import InventoryService
from utils.logger import get_logger
from models import get_session, Transaction, Product, InventoryItem as DBInventoryItem

logger = get_logger(__name__)
router = APIRouter(prefix="/api/pos", tags=["pos"])


class TransactionItem(BaseModel):
    """Individual item in a transaction."""
    product_id: str
    product_name: str
    quantity: int
    price: float
    subtotal: Optional[float] = None


class TransactionRequest(BaseModel):
    """POS transaction request."""
    items: List[TransactionItem]
    total: float
    payment_method: Optional[str] = "cash"
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    """POS transaction response."""
    transaction_id: str
    items: List[TransactionItem]
    total: float
    timestamp: str
    status: str


class TransactionHistory(BaseModel):
    """Historical transaction record with items."""
    id: str
    items: List[TransactionItem]
    total: float
    timestamp: str
    payment_method: Optional[str] = "cash"

    class Config:
        from_attributes = True


class POSStats(BaseModel):
    """POS statistics."""
    total_transactions: int
    total_revenue: float
    average_transaction_value: float
    items_sold: int
    period: str


@router.post("/transaction", response_model=TransactionResponse)
async def record_transaction(transaction: TransactionRequest) -> TransactionResponse:
    """
    Record a POS transaction.
    
    This is critical for RL feedback - each transaction at price X
    becomes a reward signal for the agent.
    
    - **transaction**: Transaction details with items and total
    
    Updates inventory, records transaction, and triggers RL feedback.
    """
    try:
        logger.info(f"Recording POS transaction with {len(transaction.items)} items, total: ${transaction.total}")
        
        session = get_session()
        pricing_service = PricingService(agent_type="ppo")
        inventory_service = InventoryService()
        
        # Consolidate items by product_id (combine duplicates)
        # e.g., [cabbage x1, tomato x2, cabbage x1] → [cabbage x2, tomato x2]
        consolidated_items = {}
        for item in transaction.items:
            if item.product_id not in consolidated_items:
                consolidated_items[item.product_id] = {
                    'product_id': item.product_id,
                    'product_name': item.product_name,
                    'quantity': 0,
                    'price': item.price,  # Use price from first occurrence
                    'subtotal': 0
                }
            consolidated_items[item.product_id]['quantity'] += item.quantity
            consolidated_items[item.product_id]['subtotal'] += item.subtotal or (item.quantity * item.price)
        
        # Generate base transaction ID (used for grouping related items)
        base_transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        recorded_items = []
        items_for_inventory = []
        transaction_ids = []  # Track all transaction IDs for this purchase
        
        # Step 1: Record consolidated transactions in database
        for idx, (product_id, consolidated_item) in enumerate(consolidated_items.items()):
            # Verify product exists
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                session.rollback()
                session.close()
                raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
            
            # Generate UNIQUE transaction ID for each distinct product
            transaction_id = f"{base_transaction_id}-{idx}-{str(uuid4())[:8]}"
            transaction_ids.append(transaction_id)
            
            # Create one transaction record per unique product (consolidated quantity)
            trans = Transaction(
                id=transaction_id,  # One ID per product type
                product_id=product_id,
                quantity=consolidated_item['quantity'],  # Consolidated quantity
                price=consolidated_item['price'],
                revenue=consolidated_item['subtotal'],
                total=consolidated_item['subtotal'],
                payment_method=transaction.payment_method,
                notes=transaction.notes,
                timestamp=datetime.now()
            )
            session.add(trans)
            session.flush()
            
            # Add consolidated item to response
            recorded_items.append(TransactionItem(
                product_id=product_id,
                product_name=consolidated_item['product_name'],
                quantity=consolidated_item['quantity'],
                price=consolidated_item['price'],
                subtotal=consolidated_item['subtotal']
            ))
            items_for_inventory.append({
                'product_id': product_id,
                'quantity': consolidated_item['quantity'],
                'price': consolidated_item['price'],
                'revenue': consolidated_item['subtotal']
            })
            
            logger.info(f"  Item: {product_id} x{consolidated_item['quantity']} @ ${consolidated_item['price']} = ${consolidated_item['subtotal']}")
        
        # Commit the main transaction FIRST
        session.commit()
        session.close()
        
        # Step 2: Update inventory AFTER main transaction commits
        # This avoids database locking issues
        for item in items_for_inventory:
            try:
                inventory_service.update_stock(
                    item['product_id'],
                    -item['quantity'],
                    reason="pos_sale"
                )
            except Exception as e:
                logger.warning(f"Failed to update inventory for {item['product_id']}: {e}")
            
            # Note: Transaction is already recorded in database (Step 1 above)
            # No need for duplicate record from pricing service
        
        logger.info(f"[OK] Transaction {base_transaction_id} recorded successfully with {len(consolidated_items)} unique items (IDs: {transaction_ids})")
        return TransactionResponse(
            transaction_id=str(base_transaction_id),  # Return the base transaction ID for grouping
            items=recorded_items,
            total=transaction.total,
            timestamp=datetime.now().isoformat(),
            status="completed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        session.close()
        logger.error(f"Error recording transaction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[TransactionHistory])
async def get_transactions(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions"),
    days: int = Query(365, ge=1, le=365, description="Days of history to retrieve")
) -> List[TransactionHistory]:
    """
    Get recent transactions with full details.
    
    - **limit**: Maximum number of transactions to return
    - **days**: Number of days of history to retrieve (default 365 = all)
    
    Returns most recent transactions in reverse chronological order with item details.
    """
    try:
        session = get_session()
        
        # Calculate date range (use local time to match transaction timestamps)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query transactions - order by timestamp DESC to get latest first
        # Don't use join in case product is deleted but transaction still exists
        transactions = session.query(Transaction).filter(
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        ).order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        result = []
        for t in transactions:
            # Try to get product name, fall back to generic if not found
            product_name = t.product_id
            product = session.query(Product).filter(Product.id == t.product_id).first()
            if product:
                product_name = product.name
            
            item = TransactionItem(
                product_id=t.product_id,
                product_name=product_name,
                quantity=t.quantity,
                price=t.price,
                subtotal=t.revenue or t.total
            )
            result.append(TransactionHistory(
                id=str(t.id),
                items=[item],
                total=t.total,
                timestamp=t.timestamp.isoformat(),
                payment_method=getattr(t, 'payment_method', 'cash')
            ))
        
        session.close()
        logger.info(f"Retrieved {len(result)} transactions")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=POSStats)
async def get_pos_stats(
    days: int = Query(30, ge=1, le=365, description="Days to analyze")
) -> POSStats:
    """
    Get POS statistics (revenue, transaction count, etc).
    
    - **days**: Number of days to include in statistics
    
    Returns aggregated sales metrics over the specified period.
    """
    try:
        session = get_session()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query transactions
        transactions = session.query(Transaction).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).all()
        
        session.close()
        
        if not transactions:
            logger.info("No transactions found for stats")
            return POSStats(
                total_transactions=0,
                total_revenue=0.0,
                average_transaction_value=0.0,
                items_sold=0,
                period=f"Last {days} days"
            )
        
        total_transactions = len(transactions)
        total_revenue = sum(t.total for t in transactions)
        average_value = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Calculate items sold
        items_sold = 0
        for t in transactions:
            if t.items:
                items_sold += len(t.items)
        
        logger.info(f"POS Stats: {total_transactions} transactions, ${total_revenue:.2f} revenue")
        return POSStats(
            total_transactions=total_transactions,
            total_revenue=total_revenue,
            average_transaction_value=average_value,
            items_sold=items_sold,
            period=f"Last {days} days"
        )
        
    except Exception as e:
        logger.error(f"Error calculating POS stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
