"""
Synthetic evaluation script for trained RL agents.

Tests trained agents without database dependencies using synthetic data.
Useful for quick evaluation and comparisons.
"""

import argparse
import logging
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

from rl.agents.ppo_agent import PPOAgent
from rl.agents.sac_agent import SACAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SyntheticEvalDataGenerator:
    """Generate realistic synthetic evaluation data."""
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed."""
        np.random.seed(seed)
    
    def generate_state_sequence(
        self,
        num_steps: int = 252,
        state_dim: int = 12
    ) -> np.ndarray:
        """
        Generate realistic 12D state sequence.
        State := [price, demand, inventory, seasonality, trend, weather, 
                 price_elasticity, competitor_price, day_of_week, inventory_ratio,
                 trend_momentum, demand_volatility]
        """
        states = []
        
        # Initialize with realistic ranges
        state = np.array([
            np.random.uniform(10, 30),      # price [10, 30]
            np.random.uniform(0, 1),        # normalized demand [0, 1]
            np.random.uniform(0, 1),        # normalized inventory [0, 1]
            np.random.uniform(0, 1),        # seasonality [0, 1]
            np.random.uniform(0, 1),        # trend [0, 1]
            np.random.uniform(0, 1),        # weather [0, 1]
            np.random.uniform(0.5, 2.5),    # price_elasticity [0.5, 2.5]
            np.random.uniform(10, 30),      # competitor_price [10, 30]
            np.random.uniform(0, 1),        # day_of_week [0, 1]
            np.random.uniform(0, 1),        # inventory_ratio [0, 1]
            np.random.uniform(-1, 1),       # trend_momentum [-1, 1]
            np.random.uniform(0, 1),        # demand_volatility [0, 1]
        ])
        
        # Generate sequence with correlation
        for _ in range(num_steps):
            # Add realistic changes
            noise = np.random.normal(0, 0.05, state_dim)
            
            # Apply constraints to maintain valid ranges
            state[0] = np.clip(state[0] + np.random.normal(0, 0.5), 10, 30)  # price
            state[1] = np.clip(state[1] + noise[1], 0, 1)  # demand
            state[2] = np.clip(state[2] + np.random.normal(-0.02, 0.03), 0, 1)  # inventory
            state[3] = np.sin(len(states) * 2 * np.pi / 252)  # seasonality (yearly cycle)
            state[4] = np.clip(state[4] + noise[4], 0, 1)  # trend
            state[5] = np.clip(state[5] + noise[5], 0, 1)  # weather
            state[6] = np.clip(state[6] + noise[6], 0.5, 2.5)  # elasticity
            state[7] = np.clip(state[7] + np.random.normal(0, 0.5), 10, 30)  # competitor
            state[8] = ((len(states) % 7) / 7)  # day_of_week cycles
            state[9] = state[2]  # inventory_ratio links to inventory
            state[10] = np.clip(state[10] + noise[10], -1, 1)  # momentum
            state[11] = np.clip(state[11] + noise[11], 0, 1)  # volatility
            
            states.append(state.copy())
        
        return np.array(states)
    
    def compute_synthetic_reward(
        self,
        price: float,
        state: np.ndarray,
        optimal_price: float = 20.0
    ) -> float:
        """Compute reward based on price and state."""
        demand = state[1]
        inventory = state[2]
        elasticity = state[6]
        
        # Demand-based reward: higher demand = higher reward
        demand_reward = demand
        
        # Price optimization reward: proximity to optimal price
        price_diff = abs(price - optimal_price)
        price_reward = max(0, 1.0 - (price_diff / optimal_price))
        
        # Inventory balance reward: middle inventory is better
        inv_reward = 1.0 - abs(inventory - 0.5) * 2
        
        # Elasticity adjustment: higher elasticity = more price-sensitive
        elasticity_factor = 1.0 / elasticity
        
        # Combined reward
        reward = (0.4 * demand_reward + 0.3 * price_reward + 0.3 * inv_reward) * elasticity_factor
        
        return float(np.clip(reward, -1, 1))


class SyntheticAgentEvaluator:
    """Synthetic evaluation for agents without environment."""
    
    def __init__(self, agent_type: str = "PPO", checkpoint_path: str = None):
        """Initialize evaluator."""
        self.agent_type = agent_type.upper()
        self.checkpoint_path = checkpoint_path
        self.agent = None
        self.data_generator = SyntheticEvalDataGenerator()
        self.eval_results = []
        
        self._initialize()
    
    def _initialize(self):
        """Initialize agent."""
        if self.agent_type == "PPO":
            self.agent = PPOAgent(state_dim=12, action_dim=1)
        else:
            self.agent = SACAgent(state_dim=12, action_dim=1)
        
        if self.checkpoint_path and Path(self.checkpoint_path).exists():
            try:
                self.agent.load_checkpoint(self.checkpoint_path)
                logger.info(f"✓ Loaded checkpoint: {self.checkpoint_path}")
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}. Using fresh agent.")
        
        logger.info(f"✓ Initialized {self.agent_type} agent")
    
    def evaluate_episode(
        self,
        num_steps: int = 252,
        deterministic: bool = True
    ) -> Dict:
        """Evaluate on synthetic episode."""
        # Generate synthetic data
        states = self.data_generator.generate_state_sequence(num_steps=num_steps)
        
        episode_reward = 0.0
        prices_selected = []
        rewards_received = []
        
        for step in range(num_steps):
            state = states[step]
            
            # Select action
            if deterministic:
                action, _, _ = self.agent.select_action(state, deterministic=True)
            else:
                action, _, _ = self.agent.select_action(state, deterministic=False)
            
            # Price is typically in [10, 30] range (from action in [-1, 1])
            price = np.clip(action[0] * 10 + 20, 10, 30)
            
            # Compute reward
            reward = self.data_generator.compute_synthetic_reward(price, state)
            
            episode_reward += reward
            prices_selected.append(float(price))
            rewards_received.append(float(reward))
        
        metrics = {
            "episode_reward": float(episode_reward),
            "episode_length": num_steps,
            "avg_reward": float(np.mean(rewards_received)),
            "std_reward": float(np.std(rewards_received)),
            "avg_price": float(np.mean(prices_selected)),
            "std_price": float(np.std(prices_selected)),
            "min_price": float(np.min(prices_selected)),
            "max_price": float(np.max(prices_selected)),
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
        """Run multiple evaluation episodes."""
        logger.info(f"\nEvaluating: {num_episodes} episodes × {num_steps_per_episode} steps")
        logger.info(f"Policy: {'Deterministic' if deterministic else 'Stochastic'}")
        
        episode_results = []
        
        for ep in range(num_episodes):
            metrics = self.evaluate_episode(
                num_steps=num_steps_per_episode,
                deterministic=deterministic
            )
            episode_results.append(metrics)
            
            if (ep + 1) % max(1, num_episodes // 5) == 0:
                logger.info(f"  Episode {ep+1}/{num_episodes} - Reward: {metrics['episode_reward']:.4f}")
        
        summary = self._aggregate_results(episode_results)
        self.eval_results = episode_results
        
        return summary
    
    def _aggregate_results(self, episode_results: List[Dict]) -> Dict:
        """Aggregate results."""
        if not episode_results:
            return {}
        
        metrics_keys = list(episode_results[0].keys())
        aggregated = {
            "num_episodes": len(episode_results),
            "timestamp": datetime.now().isoformat(),
        }
        
        for key in metrics_keys:
            values = [ep[key] for ep in episode_results]
            aggregated[f"{key}_mean"] = float(np.mean(values))
            aggregated[f"{key}_std"] = float(np.std(values))
            aggregated[f"{key}_min"] = float(np.min(values))
            aggregated[f"{key}_max"] = float(np.max(values))
        
        return aggregated
    
    def compare_agents(self, other_agent: "SyntheticAgentEvaluator", num_episodes: int = 5) -> Dict:
        """Compare this agent with another agent."""
        logger.info(f"\nComparing {self.agent_type} vs {other_agent.agent_type}")
        
        my_results = self.evaluate_multiple_episodes(
            num_episodes=num_episodes,
            deterministic=True
        )
        
        other_results = other_agent.evaluate_multiple_episodes(
            num_episodes=num_episodes,
            deterministic=True
        )
        
        comparison = {
            f"{self.agent_type}": my_results,
            f"{other_agent.agent_type}": other_results,
            "comparison": {}
        }
        
        # Calculate differences
        for key in my_results:
            if key.endswith("_mean"):
                my_val = my_results[key]
                other_val = other_results[key]
                diff = my_val - other_val
                pct_diff = (diff / abs(other_val)) * 100 if other_val != 0 else 0
                
                comparison["comparison"][key] = {
                    f"{self.agent_type}": float(my_val),
                    f"{other_agent.agent_type}": float(other_val),
                    "difference": float(diff),
                    "percent_difference": float(pct_diff),
                    "winner": self.agent_type if diff > 0 else other_agent.agent_type
                }
        
        return comparison
    
    def print_report(self, summary: Dict, agent_name: str = None):
        """Print evaluation report."""
        if agent_name is None:
            agent_name = self.agent_type
        
        logger.info("\n" + "=" * 70)
        logger.info(f"EVALUATION REPORT - {agent_name}")
        logger.info("=" * 70)
        logger.info(f"Episodes: {summary.get('num_episodes', 'N/A')}")
        logger.info("")
        
        logger.info("REWARD METRICS:")
        logger.info(f"  Mean:     {summary.get('episode_reward_mean', 0):.4f} ± {summary.get('episode_reward_std', 0):.4f}")
        logger.info(f"  Range:    [{summary.get('episode_reward_min', 0):.4f}, {summary.get('episode_reward_max', 0):.4f}]")
        
        logger.info("\nPRICE METRICS:")
        logger.info(f"  Mean:     ${summary.get('avg_price_mean', 0):.2f} ± ${summary.get('avg_price_std', 0):.2f}")
        logger.info(f"  Range:    ${summary.get('avg_price_min', 0):.2f} - ${summary.get('avg_price_max', 0):.2f}")
        
        logger.info("")
    
    def save_results(self, output_path: str = "eval_results_synthetic.json"):
        """Save results."""
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "agent_type": self.agent_type,
            "timestamp": datetime.now().isoformat(),
            "num_episodes": len(self.eval_results),
            "episodes": self.eval_results
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"✓ Results saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate agents on synthetic data")
    parser.add_argument("--agent", choices=["PPO", "SAC"], default="PPO", help="Agent to evaluate")
    parser.add_argument("--checkpoint", default=None, help="Agent checkpoint path")
    parser.add_argument("--episodes", type=int, default=10, help="Evaluation episodes")
    parser.add_argument("--steps", type=int, default=252, help="Steps per episode")
    parser.add_argument("--compare", action="store_true", help="Compare PPO vs SAC")
    parser.add_argument("--output", default="eval_results_synthetic.json", help="Output file")
    
    args = parser.parse_args()
    
    if args.compare:
        # Compare both agents
        ppo_eval = SyntheticAgentEvaluator(agent_type="PPO", checkpoint_path=args.checkpoint)
        sac_eval = SyntheticAgentEvaluator(agent_type="SAC", checkpoint_path=args.checkpoint)
        
        comparison = ppo_eval.compare_agents(sac_eval, num_episodes=10)
        
        logger.info("\n" + "=" * 70)
        logger.info("AGENT COMPARISON")
        logger.info("=" * 70)
        
        ppo_eval.print_report(comparison["PPO"], "PPO")
        sac_eval.print_report(comparison["SAC"], "SAC")
        
        logger.info("\nWINNERS BY METRIC:")
        for key, values in comparison["comparison"].items():
            logger.info(f"  {key}: {values['winner']} ({values['percent_difference']:+.1f}%)")
        
    else:
        # Single agent evaluation
        evaluator = SyntheticAgentEvaluator(
            agent_type=args.agent,
            checkpoint_path=args.checkpoint
        )
        
        summary = evaluator.evaluate_multiple_episodes(
            num_episodes=args.episodes,
            num_steps_per_episode=args.steps,
            deterministic=True
        )
        
        evaluator.print_report(summary)
        evaluator.save_results(args.output)
    
    logger.info("\n✓ Evaluation completed!")


if __name__ == "__main__":
    main()
