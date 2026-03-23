"""Checkpoint discovery and management for RL agents."""
import os
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

CHECKPOINTS_DIR = Path(__file__).parent.parent / "models" / "rl_checkpoints"


def find_latest_checkpoint(agent_type: str = None) -> Optional[str]:
    """
    Find the latest checkpoint for a given agent type, or the latest overall.
    
    Checkpoint filenames follow the pattern: {agent_type}_{timestamp}_reward{score}.pt
    
    Args:
        agent_type: Agent type to search for (ppo, sac, bandit). If None, find latest overall.
    
    Returns:
        Full path to the latest checkpoint, or None if no checkpoint found.
    """
    if not CHECKPOINTS_DIR.exists():
        logger.warning(f"Checkpoints directory not found: {CHECKPOINTS_DIR}")
        return None
    
    # Get all checkpoint files
    checkpoint_files = list(CHECKPOINTS_DIR.glob("*.pt"))
    
    if not checkpoint_files:
        logger.warning(f"No checkpoints found in {CHECKPOINTS_DIR}")
        return None
    
    # Filter by agent type if specified
    if agent_type:
        checkpoint_files = [
            f for f in checkpoint_files 
            if f.name.lower().startswith(agent_type.lower())
        ]
        
        if not checkpoint_files:
            logger.warning(f"No checkpoints found for agent type: {agent_type}")
            return None
    
    # Sort by modification time (most recent last)
    latest_checkpoint = max(checkpoint_files, key=lambda f: f.stat().st_mtime)
    
    logger.info(f"Found latest checkpoint: {latest_checkpoint.name}")
    return str(latest_checkpoint)


def list_checkpoints() -> Dict[str, List[Dict]]:
    """
    List all available checkpoints organized by agent type.
    
    Returns:
        Dictionary with agent types as keys and list of checkpoint info as values.
    """
    if not CHECKPOINTS_DIR.exists():
        logger.warning(f"Checkpoints directory not found: {CHECKPOINTS_DIR}")
        return {}
    
    checkpoints_by_type = {}
    
    for checkpoint_file in CHECKPOINTS_DIR.glob("*.pt"):
        # Parse filename: {agent_type}_{timestamp}_reward{score}.pt
        name = checkpoint_file.stem  # Remove .pt
        parts = name.split("_")
        
        if len(parts) >= 3:
            agent_type = parts[0].lower()
            # Reconstruct reward from parts (handle negative rewards)
            reward_str = "_".join(parts[2:])  # Everything after timestamp
            
            if agent_type not in checkpoints_by_type:
                checkpoints_by_type[agent_type] = []
            
            checkpoints_by_type[agent_type].append({
                "filename": checkpoint_file.name,
                "path": str(checkpoint_file),
                "modified": checkpoint_file.stat().st_mtime,
                "full_name": name
            })
    
    # Sort each agent type by modification time (most recent first)
    for agent_type in checkpoints_by_type:
        checkpoints_by_type[agent_type].sort(
            key=lambda x: x["modified"], 
            reverse=True
        )
    
    return checkpoints_by_type


def get_checkpoint_info(checkpoint_path: str) -> Optional[Dict]:
    """
    Extract agent type and reward score from checkpoint filename.
    
    Args:
        checkpoint_path: Path to checkpoint file
    
    Returns:
        Dictionary with agent_type and reward_score, or None if invalid format.
    """
    try:
        filename = Path(checkpoint_path).stem  # Remove .pt
        parts = filename.split("_")
        
        if len(parts) < 3:
            return None
        
        agent_type = parts[0].lower()
        # Look for reward in remaining parts
        reward_score = None
        for part in parts[2:]:
            if part.startswith("reward"):
                reward_score = float(part.replace("reward", ""))
                break
        
        return {
            "agent_type": agent_type,
            "reward_score": reward_score,
            "filename": Path(checkpoint_path).name
        }
    except Exception as e:
        logger.error(f"Error parsing checkpoint info: {e}")
        return None
