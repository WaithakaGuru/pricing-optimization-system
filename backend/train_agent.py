"""
Comprehensive training script for RL-based pricing agent.

Supports both:
1. Episodic training (RLTrainer) - runs full episodes
2. Live transaction training (LiveTrainer) - processes streaming transactions
"""

import argparse
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from rl.trainer import RLTrainer, LiveTrainer, ReplayBuffer
from rl.agents.ppo_agent import PPOAgent
from rl.agents.sac_agent import SACAgent
from rl.environment.price_env import PriceOptimizationEnv
from rl.environment.state_builder import StateBuilder
from services.reward_shaper import RewardShaper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_rl_agent_episodic(
    agent_type: str = "PPO",
    num_episodes: int = 50,
    checkpoint_dir: str = "models/rl_checkpoints",
    log_dir: str = "logs",
) -> dict:
    """
    Train RL agent using episodic training (standard batch RL).
    
    Args:
        agent_type: "PPO" or "SAC"
        num_episodes: Number of training episodes
        checkpoint_dir: Where to save checkpoints
        log_dir: Where to save logs
        
    Returns:
        Dictionary with training results
    """
    logger.info("=" * 70)
    logger.info(f"EPISODIC TRAINING START ({agent_type})")
    logger.info("=" * 70)
    
    # Initialize environment
    # Use valid product ID from database (p0001, p0002, ..., p0100)
    env = PriceOptimizationEnv(product_id="p0001")
    
    # Initialize agent
    if agent_type.upper() == "PPO":
        agent = PPOAgent(state_dim=12, action_dim=1)
        logger.info("✓ Initialized PPOAgent")
    else:
        agent = SACAgent(state_dim=12, action_dim=1)
        logger.info("✓ Initialized SACAgent")
    
    # Initialize trainer
    config = {
        "num_episodes": num_episodes,
        "max_steps_per_episode": 252,  # Trading days
        "update_frequency": 10,
        "eval_frequency": 5,
        "checkpoint_frequency": 10,
    }
    
    trainer = RLTrainer(
        agent=agent,
        env=env,
        config=config,
        checkpoint_dir=checkpoint_dir,
        log_dir=log_dir,
    )
    
    logger.info(f"✓ Initialized RLTrainer with config: {config}")
    
    # Run training
    try:
        trainer.train(num_episodes=num_episodes)
        
        # Get results
        results = trainer.get_results_summary()
        
        logger.info("=" * 70)
        logger.info("EPISODIC TRAINING RESULTS")
        logger.info("=" * 70)
        for key, value in results.items():
            logger.info(f"  {key}: {value}")
        
        return results
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return {}


def train_rl_agent_live(
    agent_type: str = "PPO",
    num_transactions: int = 1000,
    checkpoint_dir: str = "models/rl_checkpoints",
    log_dir: str = "logs",
) -> dict:
    """
    Train RL agent using live/streaming transaction data (LiveTrainer).
    
    Simulates real-time POS transactions and updates agent incrementally.
    
    Args:
        agent_type: "PPO" or "SAC"
        num_transactions: Number of transactions to simulate
        checkpoint_dir: Where to save checkpoints
        log_dir: Where to save logs
        
    Returns:
        Dictionary with training results
    """
    logger.info("=" * 70)
    logger.info(f"LIVE TRANSACTION-BASED TRAINING START ({agent_type})")
    logger.info("=" * 70)
    
    # Initialize components
    if agent_type.upper() == "PPO":
        agent = PPOAgent(state_dim=12, action_dim=1)
        logger.info("✓ Initialized PPOAgent")
    else:
        agent = SACAgent(state_dim=12, action_dim=1)
        logger.info("✓ Initialized SACAgent")
    
    reward_shaper = RewardShaper()
    state_builder = StateBuilder()
    
    logger.info("✓ Initialized reward shaper and state builder")
    
    # Initialize LiveTrainer
    config = {
        "update_interval": 50,  # Update agent every 50 transactions
        "buffer_capacity": 100_000,
        "batch_size": 64,
        "checkpoint_interval": 200,  # Save every 200 updates
    }
    
    trainer = LiveTrainer(
        agent=agent,
        reward_shaper=reward_shaper,
        state_builder=state_builder,
        config=config,
        checkpoint_dir=checkpoint_dir,
        log_dir=log_dir,
    )
    
    logger.info(f"✓ Initialized LiveTrainer with config: {config}")
    
    # Simulate realistic transaction stream
    logger.info(f"\nSimulating {num_transactions} transactions...")
    
    try:
        metrics_history = []
        
        # Generate synthetic transactions
        for txn_id in range(num_transactions):
            # Simulate realistic patterns
            day_of_week = (txn_id // 100) % 7
            hour_of_day = (txn_id // 10) % 24
            
            # Base demand signal with daily/hourly patterns
            base_demand = 0.5
            daily_pattern = 0.3 * np.sin(2 * np.pi * day_of_week / 7)  # Weekly pattern
            hourly_pattern = 0.2 * np.sin(2 * np.pi * hour_of_day / 24)  # Hourly pattern
            noise = np.random.normal(0, 0.05)
            demand_signal = base_demand + daily_pattern + hourly_pattern + noise
            demand_signal = np.clip(demand_signal, 0.3, 0.8)
            
            # Create transaction
            transaction = {
                "product_id": 1,
                "price": 100 + np.random.randn() * 15,  # Realistic price variation
                "quantity": int(np.random.poisson(5) + 1),  # Demand-driven quantity
                "timestamp": datetime.now() - timedelta(seconds=txn_id * 60),  # Hourly spacing
            }
            
            # Process transaction
            trainer.on_transaction(transaction)
            
            # Log progress every 100 transactions
            if (txn_id + 1) % 100 == 0:
                summary = trainer.get_performance_summary()
                metrics_history.append(summary)
                logger.info(
                    f"  Transaction {txn_id + 1}/{num_transactions} | "
                    f"Reward: {summary['mean_recent_reward']:.4f} | "
                    f"Buffer: {summary['buffer_size']} | "
                    f"Updates: {summary['total_updates']}"
                )
            
            # Check for drift
            if (txn_id + 1) % 500 == 0 and txn_id > 200:
                has_drift = trainer.detect_drift(threshold=-0.10)
                if has_drift:
                    logger.warning(f"⚠️  Performance drift detected at transaction {txn_id + 1}")
                else:
                    logger.info(f"✓ Performance stable at transaction {txn_id + 1}")
        
        # Final summary
        final_summary = trainer.get_performance_summary()
        
        logger.info("=" * 70)
        logger.info("LIVE TRAINING RESULTS")
        logger.info("=" * 70)
        logger.info(f"Total Transactions: {final_summary['total_transactions']}")
        logger.info(f"Total Updates: {final_summary['total_updates']}")
        logger.info(f"Buffer Size: {final_summary['buffer_size']}")
        logger.info(f"Mean Recent Reward: {final_summary['mean_recent_reward']:.4f}")
        logger.info(f"Std Recent Reward: {final_summary['std_recent_reward']:.4f}")
        logger.info(f"Max Recent Reward: {final_summary['max_recent_reward']:.4f}")
        logger.info(f"Min Recent Reward: {final_summary['min_recent_reward']:.4f}")
        logger.info(f"Mean All Reward: {final_summary['mean_all_reward']:.4f}")
        
        # Show reward trajectory
        if metrics_history:
            reward_trajectory = [m['mean_recent_reward'] for m in metrics_history]
            logger.info(f"\nReward Trajectory:")
            for i, r in enumerate(reward_trajectory):
                logger.info(f"  Checkpoint {i+1}: {r:.4f}")
        
        return final_summary
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        return {}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train RL pricing agent")
    parser.add_argument(
        "--mode",
        choices=["episodic", "live"],
        default="live",
        help="Training mode: episodic (batch) or live (streaming)"
    )
    parser.add_argument(
        "--agent",
        choices=["PPO", "SAC"],
        default="PPO",
        help="Agent type: PPO or SAC"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=50,
        help="Number of episodes for episodic training"
    )
    parser.add_argument(
        "--transactions",
        type=int,
        default=1000,
        help="Number of transactions for live training"
    )
    parser.add_argument(
        "--checkpoint-dir",
        default="models/rl_checkpoints",
        help="Directory to save checkpoints"
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory to save logs"
    )
    
    args = parser.parse_args()
    
    # Create directories
    Path(args.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Training Config: mode={args.mode}, agent={args.agent}")
    
    # Run training
    if args.mode == "episodic":
        results = train_rl_agent_episodic(
            agent_type=args.agent,
            num_episodes=args.episodes,
            checkpoint_dir=args.checkpoint_dir,
            log_dir=args.log_dir,
        )
    else:
        results = train_rl_agent_live(
            agent_type=args.agent,
            num_transactions=args.transactions,
            checkpoint_dir=args.checkpoint_dir,
            log_dir=args.log_dir,
        )
    
    logger.info("\n✓ Training completed successfully!")
    return results


if __name__ == "__main__":
    main()
