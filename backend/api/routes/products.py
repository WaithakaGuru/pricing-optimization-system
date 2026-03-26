"""Product endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from utils.logger import get_logger
from models import get_session, Product, InventoryItem

logger = get_logger(__name__)
router = APIRouter(prefix="/api/products", tags=["products"])


class ProductResponse(BaseModel):
    """Product response schema."""
    id: str
    name: str
    cost_price: float
    min_price: float
    max_price: float
    current_price: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CreateProductRequest(BaseModel):
    """Request to create a new product."""
    id: str
    name: str
    cost_price: float
    min_price: float
    max_price: float
    current_price: float
    initial_quantity: int = 0
    reorder_point: int = 50
    reorder_quantity: int = 100
    warehouse_location: str = "Main Warehouse"


@router.get("", response_model=List[ProductResponse])
async def list_products() -> List[ProductResponse]:
    """
    Get all products with pricing information.
    
    Returns all products with current prices, cost prices, and price ranges.
    """
    try:
        session = get_session()
        products = session.query(Product).all()
        session.close()
        
        logger.info(f"Retrieved {len(products)} products")
        return [
            ProductResponse(
                id=p.id,
                name=p.name,
                cost_price=p.cost_price,
                min_price=p.min_price,
                max_price=p.max_price,
                current_price=p.current_price,
                created_at=p.created_at.isoformat() if p.created_at else "",
                updated_at=p.updated_at.isoformat() if p.updated_at else "",
            )
            for p in products
        ]
    except Exception as e:
        logger.error(f"Error retrieving products: {e}", exc_info=True)
        return []


@router.post("", response_model=ProductResponse)
async def create_product(product: CreateProductRequest) -> ProductResponse:
    """
    Create a new product with inventory.
    
    Args:
        product: Product creation request with name, prices, cost, etc.
    
    Returns:
        Created product details
    """
    try:
        session = get_session()
        
        # Check if product already exists
        existing = session.query(Product).filter(Product.id == product.id).first()
        if existing:
            session.close()
            raise HTTPException(status_code=400, detail=f"Product {product.id} already exists")
        
        # Validate prices
        if product.min_price < 0 or product.max_price < 0 or product.current_price < 0:
            session.close()
            raise HTTPException(status_code=400, detail="Prices cannot be negative")
        
        if product.min_price > product.max_price:
            session.close()
            raise HTTPException(status_code=400, detail="Min price cannot exceed max price")
        
        if not (product.min_price <= product.current_price <= product.max_price):
            session.close()
            raise HTTPException(status_code=400, detail="Current price must be between min and max")
        
        if product.cost_price < 0:
            session.close()
            raise HTTPException(status_code=400, detail="Cost price cannot be negative")
        
        # Create product
        new_product = Product(
            id=product.id,
            name=product.name,
            cost_price=product.cost_price,
            min_price=product.min_price,
            max_price=product.max_price,
            current_price=product.current_price,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(new_product)
        session.flush()
        
        # Create inventory record
        inventory = InventoryItem(
            product_id=product.id,
            quantity=product.initial_quantity,
            reorder_point=product.reorder_point,
            reorder_quantity=product.reorder_quantity,
            warehouse_location=product.warehouse_location,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(inventory)
        
        # Commit transaction
        session.commit()
        
        # Extract values before closing session to avoid detached instance errors
        response_data = {
            'id': new_product.id,
            'name': new_product.name,
            'cost_price': new_product.cost_price,
            'min_price': new_product.min_price,
            'max_price': new_product.max_price,
            'current_price': new_product.current_price,
            'created_at': new_product.created_at.isoformat() if new_product.created_at else "",
            'updated_at': new_product.updated_at.isoformat() if new_product.updated_at else "",
        }
        session.close()
        
        logger.info(f"Created product {product.id} ({product.name}) with initial quantity {product.initial_quantity}")
        
        return ProductResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
