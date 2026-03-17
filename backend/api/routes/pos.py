"""POS transaction endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/pos", tags=["pos"])


class TransactionItem(BaseModel):
    """Individual item in a transaction."""
    product_id: str
    quantity: int
    price: float


class Transaction(BaseModel):
    """POS transaction."""
    items: List[TransactionItem]
    total: float
    timestamp: datetime


@router.post("/transaction")
async def record_transaction(transaction: Transaction) -> dict:
    """
    Record a POS transaction.
    
    This is critical for RL feedback - each transaction at price X
    becomes a reward signal for the agent.
    """
    # TODO: Store transaction, update inventory, trigger RL feedback
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/transactions")
async def get_transactions(limit: int = 100) -> list:
    """Get recent transactions."""
    # TODO: Fetch from database
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/stats")
async def get_pos_stats() -> dict:
    """Get POS statistics (revenue, transaction count, etc)."""
    # TODO: Calculate from transactions
    raise HTTPException(status_code=501, detail="Not implemented")
