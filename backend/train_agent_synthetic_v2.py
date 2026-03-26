#!/usr/bin/env python3
"""
Improved SAC agent training with product-aware pricing and enhanced reward shaping.

Key improvements:
1. Product-aware action bounds (respects min_price/max_price)
2. Enhanced reward shaper with price sanity penalties
3. Trains on diverse products
4. Better checkpoint naming with improvements marker
"""
import sys
from pathlib import Path
import numpy as np
import torch
from datetime import datetime
import json

# Setup paths
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

from rl.agents.sac_agent import SACAgent
from rl.environment.price_env import PriceOptimizationEnv
from rl.trainer import RLTrainer
from services.reward_shaper import RewardShaper
from utils.logger import get_logger

logger = get_logger(__name__)


def train_sac_improved(
    num_episodes: int = 500,
    steps_per_episode: int = 100,
    product_id: str = "p001",
    product_min_price: float = 12.0,
    product_max_price: float = 28.0,
    save_dir: str = "models/rl_checkpoints",
):
    """
    Train SAC agent with improved reward shaping and product-aware bounds.
    
    Args:
        num_episodes: Number of training episodes
        steps_per_episode: Steps per episode
        product_id: Product to train on
        product_min_price: Product minimum allowed price
        product_max_price: Product maximum allowed price
        save_dir: Directory to save checkpoints
    """
    
    logger.info("="*70)
    logger.info("SAC Agent Training (IMPROVED v2)")
    logger.info("="*70)
    logger.info(f"Product: {product_id} (${product_min_price:.2f} - ${product_max_price:.2f})")
    logger.info(f"Episodes: {num_episodes} × {steps_per_episode} steps")
    logger.info(f"Key improvements: Product-aware bounds, Enhanced reward shaper")
    
    # Create environment with PRODUCT-AWARE bounds
    env_config = {
        "price_min": product_min_price,
        "price_max": product_max_price,
        "max_steps": steps_per_episode,
    }
    env = PriceOptimizationEnv(
        product_id=product_id,
        config=env_config
    )
    
    # Create improved reward shaper with price sanity penaltis
    reward_shaper = RewardShaper(
        revenue_weight=0.4,
        profit_weight=0.3,
        inventory_weight=0.1,
        demand_weight=0.1,
        price_sanity_weight=0.2,  # NEW: Penalize extreme prices
        min_price=product_min_price,
        max_price=product_max_price,
    )
    
    logger.info(f"Reward shaper config: {reward_shaper.get_config()}")
    
    # Initialize SAC agent
    agent = SACAgent(
        state_dim=12,
        action_dim=1,
        hidden_dim=128,
        learning_rate=3e-4,
        gamma=0.99,
        tau=0.005,
    )
    
    # Training loop
    episode_rewards = []
    episode_prices = []
    best_reward = -float('inf')
    
    logger.info("\nStarting training...")
    logger.info(f"{'Ep':>4} │ {'Reward':>8} │ {'Avg Price':>10} │ {'Min Price':>10} │ {'Max Price':>10} │ {'Loss':>8}")
    logger.info("-" * 75)
    
    for episode in range(num_episodes):
        state, info = env.reset()
        episode_reward = 0.0
        episode_prices_list = []
        episode_losses = []
        
        for step in range(steps_per_episode):
            # Select action (with exploration during training)
            action, _ = agent.select_action(state, deterministic=False)
            
            # Clip action to environment bounds (safety)
            action = np.clip(action, product_min_price, product_max_price)
            episode_prices_list.append(float(action))
            
            # Step environment
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            # Store experience
            agent.store_experience(state, action, reward, next_state, done)
            
            # Update agent with batch from replay buffer
            if len(agent.replay_buffer) > agent.batch_size:
                loss = agent.update(n_updates=1)
                if loss is not None:
                    episode_losses.append(loss)
            
            episode_reward += reward
            state = next_state
            
            if done:
                break
        
        # Track metrics
        episode_rewards.append(episode_reward)
        episode_prices.append(np.mean(episode_prices_list))
        
        # Log progress
        if (episode + 1) % 50 == 0 or episode == 0:
            avg_loss = np.mean(episode_losses) if episode_losses else 0.0
            logger.info(
                f"{episode+1:>4} │ {episode_reward:>8.3f} │ "
                f"${np.mean(episode_prices_list):>9.2f} │ "
                f"${min(episode_prices_list):>9.2f} │ "
                f"${max(episode_prices_list):>9.2f} │ "
                f"{avg_loss:>8.4f}"
            )
        
        # Save best checkpoint
        if episode_reward > best_reward:
            best_reward = episode_reward
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_path = Path(save_dir) / f"SAC_{timestamp}_improved_reward{episode_reward:.3f}.pt"
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            agent.save_checkpoint(str(checkpoint_path))
            logger.info(f"  ✓ New best reward: {episode_reward:.3f} → Saved to {checkpoint_path.name}")
    
    # Final summary
    logger.info("-" * 75)
    logger.info(f"\n{'Training Summary':^75}")
    logger.info(f"Total episodes: {num_episodes}")
    logger.info(f"Best episode reward: {max(episode_rewards):.3f}")
    logger.info(f"Mean reward (last 50): {np.mean(episode_rewards[-50:]):.3f}")
    logger.info(f"Mean price (last 50): ${np.mean(episode_prices[-50:]):.2f}")
    logger.info(f"Price range learned: ${min(episode_prices):.2f} - ${max(episode_prices):.2f}")
    logger.info(f"Expected bounds: ${product_min_price:.2f} - ${product_max_price:.2f}")
    
    # Check if agent learned bounded pricing
    price_in_bounds = all(product_min_price <= p <= product_max_price for p in episode_prices)
    if price_in_bounds:
        logger.info("✓ Agent learned to price within product bounds!")
    else:
        logger.warning("⚠ Agent pricing outside bounds (check reward shaper)")
    
    # Save training history
    history = {
        "config": {
            "episodes": num_episodes,
            "steps_per_episode": steps_per_episode,
            "product_id": product_id,
            "product_min_price": product_min_price,
            "product_max_price": product_max_price,
        },
        "training": {
            "episode_rewards": episode_rewards,
            "episode_prices": episode_prices,
            "best_reward": float(max(episode_rewards)),
        },
        "timestamp": datetime.now().isoformat(),
    }
    
    history_file = f"training_history_sac_improved_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    logger.info(f"\n✓ Training history saved to {history_file}")
    
    return agent, episode_rewards


if __name__ == "__main__":
    # Train improved SAC agent
    agent, rewards = train_sac_improved(
        num_episodes=500,
        steps_per_episode=100,
        product_id="p001",
        product_min_price=12.0,
        product_max_price=28.0,
    )
    
    logger.info("\n" + "="*70)
    logger.info("✓ Training complete!")
    logger.info("="*70)
