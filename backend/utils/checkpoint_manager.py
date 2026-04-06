"""Checkpoint discovery and management for RL agents."""
import os
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

CHECKPOINTS_DIR = Path(__file__).parent.parent / "models" / "rl_checkpoints"
CHECKPOINT_METADATA_FILE = CHECKPOINTS_DIR / "checkpoint_metadata.json"


def _load_checkpoint_metadata() -> Dict:
    """Load checkpoint metadata from disk."""
    if CHECKPOINT_METADATA_FILE.exists():
        try:
            with open(CHECKPOINT_METADATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load checkpoint metadata: {e}")
    return {"checkpoints": {}}


def _save_checkpoint_metadata(metadata: Dict) -> None:
    """Save checkpoint metadata to disk."""
    try:
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(CHECKPOINT_METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save checkpoint metadata: {e}")


def register_checkpoint(
    checkpoint_path: str,
    agent_type: str,
    reward_score: float,
    metrics: Dict = None,
    is_best: bool = False
) -> None:
    """
    Register a new checkpoint with its performance metrics.
    
    Args:
        checkpoint_path: Path to checkpoint file
        agent_type: Type of agent (ppo, sac, bandit)
        reward_score: Reward score achieved
        metrics: Additional metrics (dict)
        is_best: Whether this is the best checkpoint for the agent
    """
    metadata = _load_checkpoint_metadata()
    checkpoint_name = Path(checkpoint_path).name
    
    metadata["checkpoints"][checkpoint_name] = {
        "agent_type": agent_type.lower(),
        "reward_score": float(reward_score),
        "path": str(checkpoint_path),
        "registered_at": datetime.now().isoformat(),
        "metrics": metrics or {},
        "is_best": is_best
    }
    
    _save_checkpoint_metadata(metadata)
    logger.info(f"Registered checkpoint: {checkpoint_name} (reward: {reward_score}, best: {is_best})")


def find_latest_checkpoint(agent_type: str = None) -> Optional[str]:
    """
    Find the latest checkpoint for a given agent type, or the latest overall.
    
    Checkpoint filenames follow the pattern: {agent_type}_{timestamp}_reward{score}.pt
    
    Args:
        agent_type: Agent type to search for (ppo, sac, bandit). If None, find latest overall.
    
    Returns:
        Full path to the latest checkpoint, or None if no checkpoint found.
    """
    logger.debug(f"Searching for checkpoint with agent_type={agent_type}")
    
    if not CHECKPOINTS_DIR.exists():
        logger.warning(f"❌ Checkpoints directory not found: {CHECKPOINTS_DIR}")
        return None
    
    logger.debug(f"Checkpoints directory exists: {CHECKPOINTS_DIR}")
    
    # Get all checkpoint files
    checkpoint_files = list(CHECKPOINTS_DIR.glob("*.pt"))
    
    logger.debug(f"Found {len(checkpoint_files)} checkpoint files total")
    if checkpoint_files:
        for f in checkpoint_files:
            logger.debug(f"  - {f.name}")
    
    if not checkpoint_files:
        logger.warning(f"❌ No checkpoints found in {CHECKPOINTS_DIR}")
        return None
    
    # Filter by agent type if specified
    if agent_type:
        logger.debug(f"Filtering for agent_type: {agent_type}")
        checkpoint_files = [
            f for f in checkpoint_files 
            if f.name.lower().startswith(agent_type.lower())
        ]
        
        logger.debug(f"Found {len(checkpoint_files)} checkpoints for {agent_type}")
        if checkpoint_files:
            for f in checkpoint_files:
                logger.debug(f"  - {f.name}")
        
        if not checkpoint_files:
            logger.warning(f"❌ No checkpoints found for agent type: {agent_type}")
            return None
    
    # Sort by modification time (most recent last)
    latest_checkpoint = max(checkpoint_files, key=lambda f: f.stat().st_mtime)
    
    logger.info(f"✅ Found latest checkpoint: {latest_checkpoint.name}")
    return str(latest_checkpoint)


def find_best_checkpoint(agent_type: str) -> Optional[str]:
    """
    Find the best performing checkpoint for a given agent type based on reward score.
    
    Args:
        agent_type: Agent type to search for (ppo, sac, bandit)
    
    Returns:
        Full path to the best checkpoint, or None if no checkpoint found.
    """
    if not CHECKPOINTS_DIR.exists():
        logger.warning(f"Checkpoints directory not found: {CHECKPOINTS_DIR}")
        return None
    
    checkpoint_files = list(CHECKPOINTS_DIR.glob(f"{agent_type.lower()}*.pt"))
    
    if not checkpoint_files:
        logger.warning(f"No checkpoints found for agent type: {agent_type}")
        return None
    
    # Parse reward scores from filenames and sort
    best_checkpoint = None
    best_reward = float('-inf')
    
    for checkpoint_file in checkpoint_files:
        info = get_checkpoint_info(str(checkpoint_file))
        if info and info.get("reward_score") is not None:
            if info["reward_score"] > best_reward:
                best_reward = info["reward_score"]
                best_checkpoint = checkpoint_file
    
    if best_checkpoint:
        logger.info(f"Found best checkpoint for {agent_type}: {best_checkpoint.name} (reward: {best_reward:.3f})")
        return str(best_checkpoint)
    
    return None


def list_checkpoints() -> Dict[str, List[Dict]]:
    """
    List all available checkpoints organized by agent type, sorted by reward.
    
    Returns:
        Dictionary with agent types as keys and list of checkpoint info (sorted by reward DESC).
    """
    if not CHECKPOINTS_DIR.exists():
        logger.warning(f"Checkpoints directory not found: {CHECKPOINTS_DIR}")
        return {}
    
    checkpoints_by_type = {}
    
    for checkpoint_file in CHECKPOINTS_DIR.glob("*.pt"):
        info = get_checkpoint_info(str(checkpoint_file))
        if info:
            agent_type = info["agent_type"]
            if agent_type not in checkpoints_by_type:
                checkpoints_by_type[agent_type] = []
            
            checkpoints_by_type[agent_type].append({
                "filename": checkpoint_file.name,
                "path": str(checkpoint_file),
                "agent_type": agent_type,
                "reward_score": info.get("reward_score"),
                "modified": checkpoint_file.stat().st_mtime,
                "size_mb": checkpoint_file.stat().st_size / (1024 * 1024)
            })
    
    # Sort each agent type by reward score (highest first)
    for agent_type in checkpoints_by_type:
        checkpoints_by_type[agent_type].sort(
            key=lambda x: x["reward_score"] if x["reward_score"] is not None else float('-inf'),
            reverse=True
        )
    
    return checkpoints_by_type


def get_checkpoint_info(checkpoint_path: str) -> Optional[Dict]:
    """
    Extract agent type and reward score from checkpoint filename.
    
    Filename format: {agent_type}_{timestamp}_reward{score}.pt
    Example: ppo_20260326161556_reward45.320.pt
    
    Args:
        checkpoint_path: Path to checkpoint file
    
    Returns:
        Dictionary with agent_type and reward_score, or None if invalid format.
    """
    try:
        filename = Path(checkpoint_path).stem  # Remove .pt
        parts = filename.split("_")
        
        if len(parts) < 3:
            logger.warning(f"Invalid checkpoint filename format: {filename}")
            return None
        
        agent_type = parts[0].lower()
        
        # Look for reward in remaining parts
        # Parts format: [agent_type, timestamp, rewardXXX, ...]
        reward_score = None
        for part in parts[2:]:
            if part.startswith("reward"):
                try:
                    reward_score = float(part.replace("reward", ""))
                    break
                except ValueError:
                    pass
        
        return {
            "agent_type": agent_type,
            "reward_score": reward_score,
            "filename": Path(checkpoint_path).name
        }
    except Exception as e:
        logger.error(f"Error parsing checkpoint info from {checkpoint_path}: {e}")
        return None


def cleanup_weaker_checkpoints(
    agent_type: str,
    keep_top_n: int = 3
) -> Tuple[int, int]:
    """
    Delete weaker checkpoints for an agent, keeping only the top N by reward score.
    
    Args:
        agent_type: Agent type (ppo, sac, bandit)
        keep_top_n: Number of best checkpoints to keep
    
    Returns:
        Tuple of (deleted_count, remaining_count)
    """
    if not CHECKPOINTS_DIR.exists():
        logger.warning(f"Checkpoints directory not found: {CHECKPOINTS_DIR}")
        return 0, 0
    
    checkpoints = list_checkpoints().get(agent_type.lower(), [])
    
    if len(checkpoints) <= keep_top_n:
        logger.info(f"Only {len(checkpoints)} checkpoints for {agent_type}, keeping all")
        return 0, len(checkpoints)
    
    # Keep top N, delete the rest
    to_delete = checkpoints[keep_top_n:]
    deleted_count = 0
    
    for checkpoint_info in to_delete:
        try:
            checkpoint_path = Path(checkpoint_info["path"])
            checkpoint_path.unlink()  # Delete file
            logger.info(f"Deleted: {checkpoint_info['filename']} (reward: {checkpoint_info['reward_score']:.3f})")
            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete {checkpoint_info['path']}: {e}")
    
    return deleted_count, len(checkpoints) - deleted_count


def cleanup_all_weaker_checkpoints(keep_top_n: int = 3, agent_type: str = None) -> Tuple[int, int]:
    """
    Clean up weaker checkpoints for specified agent type(s).
    
    Args:
        keep_top_n: Number of best checkpoints to keep per agent
        agent_type: Specific agent type to clean (None = all agents)
    
    Returns:
        Tuple of (total_deleted, total_remaining) across specified agents
    """
    logger.info(f"\n🧹 Cleaning up checkpoints (keeping top {keep_top_n} per agent)...")
    
    checkpoints = list_checkpoints()
    
    # Determine which agents to process
    agents_to_process = [agent_type] if agent_type else ["ppo", "sac", "bandit"]
    
    total_deleted = 0
    total_remaining = 0
    
    for agent in agents_to_process:
        if agent in checkpoints and len(checkpoints[agent]) > 0:
            deleted, remaining = cleanup_weaker_checkpoints(agent, keep_top_n)
            total_deleted += deleted
            total_remaining += remaining
            logger.info(f"  {agent.upper()}: Deleted {deleted}, Remaining {remaining}")
    
    return (total_deleted, total_remaining)


def print_checkpoint_summary() -> None:
    """Print a summary of all available checkpoints."""
    checkpoints = list_checkpoints()
    
    if not checkpoints:
        logger.info("No checkpoints found")
        return
    
    logger.info("\n📊 CHECKPOINT SUMMARY:")
    logger.info("=" * 80)
    
    for agent_type in sorted(checkpoints.keys()):
        agent_checkpoints = checkpoints[agent_type]
        logger.info(f"\n{agent_type.upper()}:")
        logger.info("-" * 80)
        
        for idx, cp in enumerate(agent_checkpoints, 1):
            is_best = "⭐ BEST" if idx == 1 else ""
            reward = cp.get("reward_score", "N/A")
            size = f"{cp.get('size_mb', 0):.2f}MB"
            logger.info(f"  {idx}. {cp['filename']:50s} | Reward: {reward:8.3f} | Size: {size:10s} {is_best}")
    
    logger.info("=" * 80)
