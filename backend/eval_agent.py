"""
Evaluation script for trained RL agents.

Tests trained pricing agents on held-out data and compares performance:
- Revenue optimization
- Demand satisfaction
- Inventory management
- Price stability
"""

import argparse
import logging
import numpy as np
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

from rl.agents.ppo_agent import PPOAgent
from rl.agents.sac_agent import SACAgent
from rl.environment.price_env import PriceOptimizationEnv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentEvaluator:
    """Comprehensive agent evaluation framework."""
    
    def __init__(self, agent_type: str = "PPO", checkpoint_path: str = None):
        """
        Initialize evaluator.
        
        Args:
            agent_type: "PPO" or "SAC"
            checkpoint_path: Path to agent checkpoint (optional)
        """
        self.agent_type = agent_type
        self.checkpoint_path = checkpoint_path
        self.agent = None
        self.env = None
        self.eval_results = []
        
        self._initialize()
    
    def _initialize(self):
        """Initialize agent and environment."""
        # Create agent
        if self.agent_type.upper() == "PPO":
            self.agent = PPOAgent(state_dim=12, action_dim=1)
        else:
            self.agent = SACAgent(state_dim=12, action_dim=1)
        
        # Load checkpoint if provided
        if self.checkpoint_path and Path(self.checkpoint_path).exists():
            try:
                self.agent.load_checkpoint(self.checkpoint_path)
                logger.info(f"✓ Loaded agent checkpoint: {self.checkpoint_path}")
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}. Using fresh agent.")
        else:
            logger.info(f"✓ Initialized fresh {self.agent_type} agent (no checkpoint)")
        
        # Create environment
        self.env = PriceOptimizationEnv()
        logger.info("✓ Initialized PriceOptimizationEnv")
    
    def evaluate_episode(self, num_steps: int = 252, deterministic: bool = True) -> Dict:
        """
        Run a single evaluation episode.
        
        Args:
            num_steps: Number of steps to evaluate (252 = trading year)
            deterministic: If True, use greedy policy (no exploration)
            
        Returns:
            Dictionary with episode metrics
        """
        state, info = self.env.reset()
        
        episode_reward = 0.0
        episode_length = 0
        prices_selected = []
        rewards_received = []
        quantities_sold = []
        revenues = []
        
        for step in range(num_steps):
            # Select action (deterministic for evaluation)
            if deterministic:
                action, _, _ = self.agent.select_action(state, deterministic=True)
            else:
                action, _, _ = self.agent.select_action(state, deterministic=False)
            
            # Step environment
            next_state, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated
            
            episode_reward += reward
            episode_length += 1
            
            # Collect metrics
            prices_selected.append(float(action))
            rewards_received.append(float(reward))
            quantities_sold.append(info.get("quantity_sold", 0))
            revenues.append(info.get("revenue", 0))
            
            state = next_state
            
            if done:
                break
        
        # Compute aggregate metrics
        metrics = {
            "episode_reward": float(episode_reward),
            "episode_length": episode_length,
            "avg_price": float(np.mean(prices_selected)),
            "std_price": float(np.std(prices_selected)),
            "min_price": float(np.min(prices_selected)),
            "max_price": float(np.max(prices_selected)),
            "avg_reward": float(np.mean(rewards_received)),
            "std_reward": float(np.std(rewards_received)),
            "total_revenue": float(np.sum(revenues)),
            "avg_revenue_per_step": float(np.mean(revenues)),
            "total_quantity_sold": int(np.sum(quantities_sold)),
            "avg_quantity_per_step": float(np.mean(quantities_sold)),
            "reward_max": float(np.max(rewards_received)),
            "reward_min": float(np.min(rewards_received)),
        }
        
        return metrics
    
    def evaluate_multiple_episodes(
        self,
        num_episodes: int = 10,
        num_steps_per_episode: int = 252,
        deterministic: bool = True
    ) -> Dict:
        """
        Run multiple evaluation episodes.
        
        Args:
            num_episodes: Number of evaluation episodes
            num_steps_per_episode: Steps per episode
            deterministic: If True, use greedy policy
            
        Returns:
            Summary dictionary with aggregated metrics
        """
        logger.info(f"\nRunning evaluation: {num_episodes} episodes × {num_steps_per_episode} steps")
        logger.info(f"Policy: {'Deterministic (greedy)' if deterministic else 'Stochastic'}")
        
        episode_results = []
        
        for ep in range(num_episodes):
            metrics = self.evaluate_episode(
                num_steps=num_steps_per_episode,
                deterministic=deterministic
            )
            episode_results.append(metrics)
            
            if (ep + 1) % max(1, num_episodes // 5) == 0:
                logger.info(f"  Episode {ep+1}/{num_episodes} - Reward: {metrics['episode_reward']:.3f}")
        
        # Aggregate results
        summary = self._aggregate_results(episode_results)
        self.eval_results = episode_results
        
        return summary
    
    def _aggregate_results(self, episode_results: List[Dict]) -> Dict:
        """Aggregate results from multiple episodes."""
        if not episode_results:
            return {}
        
        # Extract all metric names
        metrics_keys = list(episode_results[0].keys())
        
        aggregated = {
            "num_episodes": len(episode_results),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Aggregate each metric
        for key in metrics_keys:
            values = [ep[key] for ep in episode_results]
            
            aggregated[f"{key}_mean"] = float(np.mean(values))
            aggregated[f"{key}_std"] = float(np.std(values))
            aggregated[f"{key}_min"] = float(np.min(values))
            aggregated[f"{key}_max"] = float(np.max(values))
        
        return aggregated
    
    def compare_deterministic_vs_stochastic(self, num_episodes: int = 5) -> Dict:
        """
        Compare deterministic (greedy) vs stochastic (explore) policies.
        
        Args:
            num_episodes: Episodes per policy
            
        Returns:
            Comparison results
        """
        logger.info("\n" + "=" * 70)
        logger.info("DETERMINISTIC vs STOCHASTIC POLICY COMPARISON")
        logger.info("=" * 70)
        
        # Evaluate deterministic
        det_results = self.evaluate_multiple_episodes(
            num_episodes=num_episodes,
            deterministic=True
        )
        
        # Evaluate stochastic
        stoch_results = self.evaluate_multiple_episodes(
            num_episodes=num_episodes,
            deterministic=False
        )
        
        # Compare
        comparison = {
            "deterministic": det_results,
            "stochastic": stoch_results,
            "differences": {}
        }
        
        # Calculate differences
        for key in det_results:
            if key.endswith("_mean"):
                det_val = det_results[key]
                stoch_val = stoch_results[key]
                diff = det_val - stoch_val
                pct_diff = (diff / abs(stoch_val)) * 100 if stoch_val != 0 else 0
                comparison["differences"][key] = {
                    "absolute": float(diff),
                    "percent": float(pct_diff)
                }
        
        return comparison
    
    def print_evaluation_report(self, summary: Dict):
        """Print formatted evaluation report."""
        logger.info("\n" + "=" * 70)
        logger.info("EVALUATION REPORT")
        logger.info("=" * 70)
        logger.info(f"Agent Type: {self.agent_type}")
        logger.info(f"Episodes: {summary.get('num_episodes', 'N/A')}")
        logger.info("")
        
        # Reward metrics
        logger.info("REWARD METRICS:")
        logger.info(f"  Mean Reward:     {summary.get('episode_reward_mean', 0):.4f} ± {summary.get('episode_reward_std', 0):.4f}")
        logger.info(f"  Reward Range:    [{summary.get('episode_reward_min', 0):.4f}, {summary.get('episode_reward_max', 0):.4f}]")
        
        # Price metrics
        logger.info("\nPRICE METRICS:")
        logger.info(f"  Mean Price:      ${summary.get('avg_price_mean', 0):.2f} ± ${summary.get('avg_price_std', 0):.2f}")
        logger.info(f"  Price Range:     ${summary.get('avg_price_min', 0):.2f} - ${summary.get('avg_price_max', 0):.2f}")
        logger.info(f"  Price Variance:  ${summary.get('std_price_mean', 0):.2f}")
        
        # Revenue metrics
        logger.info("\nREVENUE METRICS:")
        logger.info(f"  Total Revenue:   ${summary.get('total_revenue_mean', 0):.2f} ± ${summary.get('total_revenue_std', 0):.2f}")
        logger.info(f"  Avg/Step:        ${summary.get('avg_revenue_per_step_mean', 0):.2f}")
        
        # Sales metrics
        logger.info("\nSALES METRICS:")
        logger.info(f"  Total Quantity:  {summary.get('total_quantity_sold_mean', 0):.1f} ± {summary.get('total_quantity_sold_std', 0):.1f}")
        logger.info(f"  Avg/Step:        {summary.get('avg_quantity_per_step_mean', 0):.2f}")
        
        logger.info("")
    
    def save_results(self, output_path: str = "eval_results.json"):
        """Save evaluation results to file."""
        if not self.eval_results:
            logger.warning("No evaluation results to save")
            return
        
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        data = {
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
            "num_episodes": len(self.eval_results),
            "episodes": self.eval_results
        }
        
        # Save as JSON
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✓ Results saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate trained RL agents")
    parser.add_argument(
        "--agent",
        choices=["PPO", "SAC"],
        default="PPO",
        help="Agent type to evaluate"
    )
    parser.add_argument(
        "--checkpoint",
        default=None,
        help="Path to agent checkpoint"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=10,
        help="Number of evaluation episodes"
    )
    parser.add_argument(
        "--steps-per-episode",
        type=int,
        default=252,
        help="Steps per episode"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare deterministic vs stochastic policies"
    )
    parser.add_argument(
        "--output",
        default="eval_results.json",
        help="Output file for results"
    )
    
    args = parser.parse_args()
    
    # Create evaluator
    evaluator = AgentEvaluator(agent_type=args.agent, checkpoint_path=args.checkpoint)
    
    if args.compare:
        # Compare policies
        comparison = evaluator.compare_deterministic_vs_stochastic(num_episodes=5)
        
        logger.info("\n" + "=" * 70)
        logger.info("POLICY COMPARISON RESULTS")
        logger.info("=" * 70)
        logger.info("Deterministic Metrics:")
        evaluator.print_evaluation_report(comparison["deterministic"])
        logger.info("\nStochastic Metrics:")
        evaluator.print_evaluation_report(comparison["stochastic"])
        
    else:
        # Standard evaluation
        summary = evaluator.evaluate_multiple_episodes(
            num_episodes=args.episodes,
            num_steps_per_episode=args.steps_per_episode,
            deterministic=True
        )
        
        evaluator.print_evaluation_report(summary)
    
    # Save results
    evaluator.save_results(args.output)
    
    logger.info("\n✓ Evaluation completed!")


if __name__ == "__main__":
    main()
