"""RL Training Loop and Checkpointing."""
import torch
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, List
import json
from datetime import datetime
from rl.environment.price_env import PriceOptimizationEnv

logger = logging.getLogger(__name__)


class RLTrainer:
    """
    Orchestrates RL agent training.
    
    **Responsibilities:**
    - Runs training episodes in PriceOptimizationEnv
    - Collects experience and manages batches
    - Updates agents (PPO or SAC)
    - Logs metrics and saves checkpoints
    - Integrates with experiment tracking (optional: W&B, MLflow)
    
    **Workflow:**
    1. Initialize environment and agent
    2. Run episodes: collect states, actions, rewards, next_states
    3. Update agent: process experience
    4. Log metrics: episode reward, loss, KPIs
    5. Save checkpoints periodically
    6. Evaluate: run test episodes without exploration
    """

    def __init__(
        self,
        agent,
        env: PriceOptimizationEnv,
        config: Dict = None,
        log_dir: str = "logs",
        checkpoint_dir: str = "models/rl_checkpoints",
    ):
        """
        Initialize trainer.
        
        Args:
            agent: RL agent (PPOAgent or SACAgent)
            env: Gymnasium environment
            config: Training hyperparameters
            log_dir: Directory for training logs
            checkpoint_dir: Directory for model checkpoints
        """
        self.agent = agent
        self.env = env
        self.config = config or {}
        
        # Directories
        self.log_dir = Path(log_dir)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Training parameters
        self.num_episodes = self.config.get("num_episodes", 100)
        self.max_steps_per_episode = self.config.get("max_steps_per_episode", 252)
        self.update_frequency = self.config.get("update_frequency", 10)  # Updates per N episodes
        self.eval_frequency = self.config.get("eval_frequency", 20)
        self.checkpoint_frequency = self.config.get("checkpoint_frequency", 50)
        
        # Metrics tracking
        self.episode_rewards = []
        self.episode_lengths = []
        self.policy_losses = []
        self.value_losses = []
        self.episode_metrics = []
        
        # Training state
        self.current_episode = 0
        self.total_steps = 0
        self.best_reward = -np.inf
        
        logger.info(f"RLTrainer initialized with config: {config}")

    def train(self, num_episodes: Optional[int] = None):
        """
        Run training loop.
        
        Args:
            num_episodes: Number of episodes to train (overrides config)
        """
        num_episodes = num_episodes or self.num_episodes
        logger.info(f"Starting training for {num_episodes} episodes")
        
        for episode in range(num_episodes):
            self.current_episode = episode
            
            # Run episode
            episode_reward, episode_length, metrics = self._run_episode(training=True)
            
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(episode_length)
            self.episode_metrics.append(metrics)
            
            # Update agent
            if (episode + 1) % self.update_frequency == 0:
                self._update_agent()
            
            # Evaluate
            if (episode + 1) % self.eval_frequency == 0:
                eval_reward = self._evaluate(num_eval_episodes=5)
                logger.info(
                    f"Episode {episode + 1}/{num_episodes} - "
                    f"Train Reward: {episode_reward:.3f}, "
                    f"Eval Reward: {eval_reward:.3f}"
                )
            
            # Save checkpoint
            if (episode + 1) % self.checkpoint_frequency == 0:
                self._save_checkpoint(episode + 1)
        
        logger.info("Training completed")
        self._save_training_history()

    def _run_episode(self, training: bool = True) -> tuple:
        """
        Run a single episode and collect experience.
        
        Args:
            training: If True, store experience for updates. If False, just evaluate.
        
        Returns:
            (episode_reward, episode_length, metrics_dict)
        """
        state, info = self.env.reset()
        episode_reward = 0.0
        episode_length = 0
        metrics = {
            "prices_selected": [],
            "rewards_received": [],
            "inventories": [],
        }
        
        for step in range(self.max_steps_per_episode):
            # Select action
            if training:
                action, log_prob, value = self.agent.select_action(state)
            else:
                action, log_prob, value = self.agent.select_action(state, deterministic=True)
            
            # Step environment
            next_state, reward, terminated, truncated, step_info = self.env.step(action)
            done = terminated or truncated
            
            episode_reward += reward
            episode_length += 1
            self.total_steps += 1
            
            # Store experience
            if training and hasattr(self.agent, 'store_experience'):
                self.agent.store_experience(state, action, reward, log_prob, value, done)
            elif training and hasattr(self.agent, 'store_experience'):
                # SAC: store different format
                self.agent.store_experience(state, action, reward, next_state, done)
            
            # Track metrics
            metrics["prices_selected"].append(float(action))
            metrics["rewards_received"].append(float(reward))
            metrics["inventories"].append(step_info.get("inventory", 0))
            
            state = next_state
            
            if done:
                break
        
        # Compute aggregate metrics
        metrics["avg_price"] = np.mean(metrics["prices_selected"])
        metrics["avg_reward"] = np.mean(metrics["rewards_received"])
        metrics["final_inventory"] = metrics["inventories"][-1] if metrics["inventories"] else 0
        
        return episode_reward, episode_length, metrics

    def _update_agent(self):
        """Update agent with collected experience."""
        if hasattr(self.agent, 'update'):
            try:
                # PPO has update() method
                if hasattr(self.agent, 'actor'):  # Both PPO and SAC have this
                    if hasattr(self.agent, 'clear_buffer'):  # PPO signature
                        self.agent.update()
                    else:  # SAC signature
                        self.agent.update(n_updates=10)  # Multiple SAC updates
                
                logger.debug("Agent updated successfully")
            except Exception as e:
                logger.error(f"Error during agent update: {e}", exc_info=True)
        else:
            logger.warning("Agent does not have update method")

    def _evaluate(self, num_eval_episodes: int = 5) -> float:
        """
        Evaluate agent on test episodes (no learning).
        
        Args:
            num_eval_episodes: Number of episodes to evaluate
        
        Returns:
            Average reward across eval episodes
        """
        eval_rewards = []
        
        for _ in range(num_eval_episodes):
            episode_reward, _, _ = self._run_episode(training=False)
            eval_rewards.append(episode_reward)
        
        avg_eval_reward = np.mean(eval_rewards)
        
        # Track best performance
        if avg_eval_reward > self.best_reward:
            self.best_reward = avg_eval_reward
            self._save_checkpoint(self.current_episode, is_best=True)
        
        return avg_eval_reward

    def _save_checkpoint(self, episode: int, is_best: bool = False):
        """
        Save agent checkpoint and metrics.
        
        Args:
            episode: Episode number
            is_best: If True, save as best checkpoint
        """
        suffix = "_best" if is_best else f"_{episode}"
        checkpoint_path = self.checkpoint_dir / f"agent{suffix}.pt"
        
        try:
            self.agent.save_checkpoint(str(checkpoint_path))
            logger.info(f"Checkpoint saved: {checkpoint_path}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def _save_training_history(self):
        """Save training history and metrics."""
        history = {
            "episode_rewards": self.episode_rewards,
            "episode_lengths": self.episode_lengths,
            "best_reward": float(self.best_reward),
            "total_steps": self.total_steps,
            "timestamp": datetime.now().isoformat(),
        }
        
        history_path = self.log_dir / "training_history.json"
        try:
            with open(history_path, "w") as f:
                json.dump(history, f, indent=2)
            logger.info(f"Training history saved: {history_path}")
        except Exception as e:
            logger.error(f"Failed to save training history: {e}")
        
        # Also save episode metrics
        metrics_path = self.log_dir / "episode_metrics.json"
        try:
            with open(metrics_path, "w") as f:
                json.dump(self.episode_metrics, f, indent=2)
            logger.info(f"Episode metrics saved: {metrics_path}")
        except Exception as e:
            logger.error(f"Failed to save episode metrics: {e}")

    def get_results_summary(self) -> Dict:
        """Get summary of training results."""
        if not self.episode_rewards:
            return {}
        
        return {
            "total_episodes": len(self.episode_rewards),
            "total_steps": self.total_steps,
            "mean_episode_reward": float(np.mean(self.episode_rewards[-20:])),
            "best_episode_reward": float(np.max(self.episode_rewards)),
            "worst_episode_reward": float(np.min(self.episode_rewards)),
            "mean_episode_length": float(np.mean(self.episode_lengths)),
            "best_eval_reward": float(self.best_reward),
        }

    def plot_training_progress(self, save_path: Optional[str] = None):
        """
        Plot training progress: rewards and lengths over episodes.
        
        Args:
            save_path: Path to save plot (optional)
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("Matplotlib not available for plotting")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        
        # Episode rewards
        axes[0].plot(self.episode_rewards, alpha=0.7, label="Episode Reward")
        axes[0].set_xlabel("Episode")
        axes[0].set_ylabel("Reward")
        axes[0].set_title("Training Rewards")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Episode lengths
        axes[1].plot(self.episode_lengths, alpha=0.7, color="orange", label="Episode Length")
        axes[1].set_xlabel("Episode")
        axes[1].set_ylabel("Steps")
        axes[1].set_title("Episode Lengths")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=100)
            logger.info(f"Training progress plot saved: {save_path}")
        else:
            plt.show()
        
        plt.close()
        # TODO: Save agent weights and metadata
        logger.info(f"Saved checkpoint at episode {episode}")

    def load_checkpoint(self, checkpoint_id: str):
        """Load a saved checkpoint."""
        # TODO: Load agent weights
        logger.info(f"Loaded checkpoint {checkpoint_id}")
