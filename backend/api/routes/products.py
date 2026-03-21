"""Product endpoints."""
from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from utils.logger import get_logger
from models import get_session, Product

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
