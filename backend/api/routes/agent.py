"""RL agent control endpoints."""
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/train")
async def trigger_training() -> dict:
    """Trigger RL agent training or retraining."""
    # TODO: Queue training job with Celery
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/metrics")
async def get_agent_metrics() -> dict:
    """Get RL agent performance metrics (rewards, policy updates, etc)."""
    # TODO: Fetch from MLflow or W&B
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/policy")
async def get_agent_policy() -> dict:
    """Get current agent policy state."""
    # TODO: Return current policy weights/state
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/checkpoint/{checkpoint_id}")
async def load_checkpoint(checkpoint_id: str) -> dict:
    """Load a saved agent checkpoint."""
    # TODO: Load from models/rl_checkpoints/
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/status")
async def get_agent_status() -> dict:
    """Get agent training status."""
    # TODO: Check if training is running, return metrics
    raise HTTPException(status_code=501, detail="Not implemented")
