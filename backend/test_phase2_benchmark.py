"""Integration test comparing Phase 1 Bandit vs Phase 2 Agents (PPO & SAC)."""
import numpy as np
import logging
from pathlib import Path
import json
from datetime import datetime

from rl.agents.bandit import ContextualBandit
from rl.agents.ppo_agent import PPOAgent
from rl.agents.sac_agent import SACAgent
from rl.environment.price_env import PriceOptimizationEnv
from rl.trainer import RLTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentBenchmark:
    """Compare performance of different RL agents."""
    
    def __init__(self, num_episodes: int = 20, max_steps: int = 100):
        self.num_episodes = num_episodes
        self.max_steps = max_steps
        self.results = {}
    
    def run_bandit_baseline(self):
        """Run contextual bandit as baseline."""
        logger.info("\n" + "=" * 60)
        logger.info("Running Contextual Bandit (Phase 1)")
        logger.info("=" * 60)
        
        env = PriceOptimizationEnv(product_id="BENCHMARK-BANDIT", max_steps=self.max_steps)
        bandit = ContextualBandit(n_arms=20, algorithm="ucb")
        
        episode_rewards = []
        
        for episode in range(self.num_episodes):
            state, info = env.reset()
            episode_reward = 0
            
            for step in range(self.max_steps):
                arm = bandit.select_arm(state)
                action = bandit.prices[arm]
                next_state, reward, terminated, truncated, info = env.step(action)
                
                bandit.update(arm, reward)
                episode_reward += reward
                state = next_state
                
                if terminated or truncated:
                    break
            
            episode_rewards.append(episode_reward)
            logger.info(f"Episode {episode + 1}/{self.num_episodes}: Reward={episode_reward:.3f}")
        
        self.results["bandit"] = {
            "mean_reward": float(np.mean(episode_rewards)),
            "std_reward": float(np.std(episode_rewards)),
            "max_reward": float(np.max(episode_rewards)),
            "min_reward": float(np.min(episode_rewards)),
            "episode_rewards": episode_rewards,
        }
        
        logger.info(f"Bandit Results: Mean={self.results['bandit']['mean_reward']:.3f} ± {self.results['bandit']['std_reward']:.3f}")
    
    def run_ppo_agent(self):
        """Run PPO agent."""
        logger.info("\n" + "=" * 60)
        logger.info("Running PPO Agent (Phase 2)")
        logger.info("=" * 60)
        
        env = PriceOptimizationEnv(product_id="BENCHMARK-PPO", max_steps=self.max_steps)
        agent = PPOAgent(state_dim=12, action_dim=1, hidden_dim=128, n_epochs=5)
        
        config = {
            "num_episodes": self.num_episodes,
            "max_steps_per_episode": self.max_steps,
            "update_frequency": 2,
            "eval_frequency": self.num_episodes + 1,
            "checkpoint_frequency": self.num_episodes + 1,
        }
        
        trainer = RLTrainer(agent, env, config=config)
        trainer.train(num_episodes=self.num_episodes)
        
        summary = trainer.get_results_summary()
        self.results["ppo"] = {
            "mean_reward": summary.get("mean_episode_reward", 0),
            "best_reward": summary.get("best_episode_reward", 0),
            "worst_reward": summary.get("worst_episode_reward", 0),
            "total_steps": summary.get("total_steps", 0),
            "episode_rewards": trainer.episode_rewards,
        }
        
        logger.info(f"PPO Results: Mean={self.results['ppo']['mean_reward']:.3f}, Best={self.results['ppo']['best_reward']:.3f}")
    
    def run_sac_agent(self):
        """Run SAC agent."""
        logger.info("\n" + "=" * 60)
        logger.info("Running SAC Agent (Phase 2 Alt)")
        logger.info("=" * 60)
        
        env = PriceOptimizationEnv(product_id="BENCHMARK-SAC", max_steps=self.max_steps)
        agent = SACAgent(state_dim=12, action_dim=1, hidden_dim=128)
        
        config = {
            "num_episodes": self.num_episodes,
            "max_steps_per_episode": self.max_steps,
            "update_frequency": 2,
            "eval_frequency": self.num_episodes + 1,
            "checkpoint_frequency": self.num_episodes + 1,
        }
        
        trainer = RLTrainer(agent, env, config=config)
        trainer.train(num_episodes=self.num_episodes)
        
        summary = trainer.get_results_summary()
        self.results["sac"] = {
            "mean_reward": summary.get("mean_episode_reward", 0),
            "best_reward": summary.get("best_episode_reward", 0),
            "worst_reward": summary.get("worst_episode_reward", 0),
            "total_steps": summary.get("total_steps", 0),
            "episode_rewards": trainer.episode_rewards,
        }
        
        logger.info(f"SAC Results: Mean={self.results['sac']['mean_reward']:.3f}, Best={self.results['sac']['best_reward']:.3f}")
    
    def print_comparison(self):
        """Print comparison of all agents."""
        logger.info("\n" + "=" * 60)
        logger.info("Agent Comparison Summary")
        logger.info("=" * 60)
        
        comparison_data = {}
        
        for agent_name, metrics in self.results.items():
            mean_reward = metrics.get("mean_reward", 0)
            comparison_data[agent_name] = mean_reward
            
            logger.info(f"\n{agent_name.upper()}:")
            for key, value in metrics.items():
                if key != "episode_rewards":
                    logger.info(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")
        
        # Rank agents
        ranked = sorted(comparison_data.items(), key=lambda x: x[1], reverse=True)
        logger.info("\nRanking (by mean reward):")
        for rank, (agent_name, reward) in enumerate(ranked, 1):
            logger.info(f"  {rank}. {agent_name.upper()}: {reward:.3f}")
    
    def save_results(self, output_dir: str = "results"):
        """Save comparison results to file."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Make results JSON serializable
        results_to_save = {}
        for agent_name, metrics in self.results.items():
            results_to_save[agent_name] = {
                k: (v.tolist() if isinstance(v, np.ndarray) else v)
                for k, v in metrics.items()
            }
        
        with open(results_file, "w") as f:
            json.dump(results_to_save, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")


def test_phase2_agents():
    """Main test function."""
    logger.info("✓ Starting Phase 2 Agent Benchmark Test")
    
    benchmark = AgentBenchmark(num_episodes=10, max_steps=100)
    
    # Run all agents
    try:
        benchmark.run_bandit_baseline()
        logger.info("✓ Bandit baseline completed")
    except Exception as e:
        logger.error(f"✗ Bandit failed: {e}", exc_info=True)
    
    try:
        benchmark.run_ppo_agent()
        logger.info("✓ PPO agent training completed")
    except Exception as e:
        logger.error(f"✗ PPO failed: {e}", exc_info=True)
    
    try:
        benchmark.run_sac_agent()
        logger.info("✓ SAC agent training completed")
    except Exception as e:
        logger.error(f"✗ SAC failed: {e}", exc_info=True)
    
    # Print results
    benchmark.print_comparison()
    benchmark.save_results()
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ Phase 2 Benchmark Test Completed Successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_phase2_agents()
