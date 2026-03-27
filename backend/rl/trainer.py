"""RL Training Loop and Checkpointing."""
import torch
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, List
import json
from datetime import datetime
from collections import deque
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
            if training:
                # Check agent type to call correct store_experience signature
                agent_class_name = type(self.agent).__name__
                if agent_class_name == "SACAgent":
                    # SAC: off-policy, needs next_state
                    self.agent.store_experience(state, action, reward, next_state, done)
                else:
                    # PPO/other: on-policy, needs log_prob and value
                    self.agent.store_experience(state, action, reward, log_prob, value, done)
            
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
        Save agent checkpoint with proper naming convention.
        
        Checkpoint naming: {agent_type}_{timestamp}_reward{score}.pt
        Example: PPO_20260327_120534_reward154.32.pt
        
        Args:
            episode: Episode number
            is_best: If True, also save as best checkpoint
        """
        # Get agent type from class name (PPOAgent -> PPO, SACAgent -> SAC)
        agent_type = type(self.agent).__name__.replace("Agent", "")
        
        # Get current best reward for this episode
        current_reward = self.best_reward if self.best_reward != -np.inf else 0.0
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build checkpoint filename
        checkpoint_name = f"{agent_type}_{timestamp}_reward{current_reward:.3f}.pt"
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        
        try:
            self.agent.save_checkpoint(str(checkpoint_path))
            logger.info(f"Checkpoint saved: {checkpoint_path.name} (reward: {current_reward:.3f})")
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


class LiveTrainer:
    """
    Live training loop for deployed pricing agents.
    
    **Workflow:**
    1. Observe POS transaction (price applied, quantity sold)
    2. Extract state (product features, inventory, weather, etc.)
    3. Calculate reward (revenue, margin, inventory impact)
    4. Store (state, action, reward) in replay buffer
    5. Periodically update agent (every N transactions)
    6. Save checkpoints (daily or after N updates)
    
    **Features:**
    - Non-blocking: operates alongside live sales
    - Graceful learning: handles sparse feedback
    - Drift detection: monitors performance degradation
    - Checkpoint versioning: maintains model history
    """

    def __init__(
        self,
        agent,
        reward_shaper,
        state_builder,
        config: Dict = None,
        checkpoint_dir: str = "models/rl_checkpoints",
        log_dir: str = "logs",
    ):
        """
        Initialize live trainer.
        
        Args:
            agent: RL agent (PPOAgent or SACAgent)
            reward_shaper: RewardShaper for computing rewards
            state_builder: StateBuilder for extracting state from transactions
            config: Training config (update frequency, buffer size, etc.)
            checkpoint_dir: Directory for model checkpoints
            log_dir: Directory for logs
        """
        self.agent = agent
        self.reward_shaper = reward_shaper
        self.state_builder = state_builder
        self.config = config or {}
        
        self.checkpoint_dir = Path(checkpoint_dir)
        self.log_dir = Path(log_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Hyperparameters
        self.update_interval = self.config.get("update_interval", 50)  # Update every N transactions
        self.buffer_capacity = self.config.get("buffer_capacity", 100_000)
        self.batch_size = self.config.get("batch_size", 64)
        self.checkpoint_interval = self.config.get("checkpoint_interval", 500)  # Save every N updates
        
        # State tracking
        self.replay_buffer = []
        self.transaction_count = 0
        self.update_count = 0
        self.prev_state = None
        self.live_rewards = []
        self.update_metrics = []
        
        # Performance tracking
        self.performance_window = deque(maxlen=100)  # Last 100 transactions
        
        logger.info(f"LiveTrainer initialized (buffer_size={self.buffer_capacity}, update_interval={self.update_interval})")

    def on_transaction(self, transaction: Dict):
        """
        Called when a new POS transaction occurs.
        
        Args:
            transaction: Dict with keys:
                - product_id: Product identifier
                - price: Price at which item was sold
                - quantity: Quantity sold
                - timestamp: Transaction timestamp
        """
        try:
            product_id = transaction["product_id"]
            
            # Extract state
            state = self.state_builder.build_state(product_id)
            
            # Compute reward
            reward = self.reward_shaper.compute_reward(
                prev_state=self.prev_state,
                action=transaction.get("price", 0.0),
                curr_state=state,
                transaction=transaction,
            )
            
            # Store experience
            experience = {
                "product_id": product_id,
                "state": state,
                "action": transaction.get("price", 0.0),
                "reward": reward,
                "done": False,
                "timestamp": transaction.get("timestamp", datetime.utcnow()),
            }
            
            self.replay_buffer.append(experience)
            self.transaction_count += 1
            self.live_rewards.append(reward)
            self.performance_window.append(reward)
            
            # Keep buffer size under control
            if len(self.replay_buffer) > self.buffer_capacity:
                self.replay_buffer.pop(0)
            
            # Update state for next transaction
            self.prev_state = state
            
            # Periodic agent update
            if self.transaction_count % self.update_interval == 0:
                self._update_agent()
                self.update_count += 1
                
                # Periodic checkpoint
                if self.update_count % self.checkpoint_interval == 0:
                    self._save_checkpoint()
            
            logger.debug(f"Transaction {self.transaction_count}: reward={reward:.3f}, buffer_size={len(self.replay_buffer)}")
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}", exc_info=True)

    def _update_agent(self):
        """Update agent with buffered experiences."""
        if len(self.replay_buffer) < self.batch_size:
            logger.debug(f"Buffer too small ({len(self.replay_buffer)} < {self.batch_size}), skipping update")
            return
        
        try:
            # Sample batch from buffer
            batch_indices = np.random.choice(len(self.replay_buffer), size=self.batch_size, replace=False)
            batch = [self.replay_buffer[i] for i in batch_indices]
            
            # Prepare training data
            states = np.array([exp["state"] for exp in batch])
            actions = np.array([exp["action"] for exp in batch])
            rewards = np.array([exp["reward"] for exp in batch])
            
            # Update agent
            if hasattr(self.agent, 'update_from_batch'):
                loss_info = self.agent.update_from_batch(states, actions, rewards)
                
                metric = {
                    "update_num": self.update_count,
                    "transaction_num": self.transaction_count,
                    "batch_size": self.batch_size,
                    "avg_batch_reward": float(np.mean(rewards)),
                    "avg_recent_reward": float(np.mean(list(self.performance_window))),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                
                if isinstance(loss_info, dict):
                    metric.update(loss_info)
                
                self.update_metrics.append(metric)
                
                logger.info(
                    f"Update {self.update_count} (txn {self.transaction_count}): "
                    f"batch_reward={metric['avg_batch_reward']:.3f}, "
                    f"recent_reward={metric['avg_recent_reward']:.3f}"
                )
            else:
                logger.warning("Agent does not have update_from_batch method")
                
        except Exception as e:
            logger.error(f"Error updating agent: {e}", exc_info=True)

    def _save_checkpoint(self):
        """Save agent checkpoint."""
        try:
            checkpoint_name = f"agent_v{self.update_count}.pt"
            checkpoint_path = self.checkpoint_dir / checkpoint_name
            
            self.agent.save_checkpoint(str(checkpoint_path))
            
            logger.info(f"Checkpoint saved: {checkpoint_path}")
            
            # Also save live training metrics
            metrics_path = self.log_dir / "live_training_metrics.json"
            with open(metrics_path, "w") as f:
                json.dump(self.update_metrics[-100:], f, indent=2)  # Last 100 updates
                
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}", exc_info=True)

    def get_performance_summary(self) -> Dict:
        """Get current performance metrics."""
        if not self.live_rewards:
            return {}
        
        recent_rewards = list(self.performance_window)
        
        return {
            "total_transactions": self.transaction_count,
            "total_updates": self.update_count,
            "buffer_size": len(self.replay_buffer),
            "mean_recent_reward": float(np.mean(recent_rewards)) if recent_rewards else 0.0,
            "std_recent_reward": float(np.std(recent_rewards)) if len(recent_rewards) > 1 else 0.0,
            "max_recent_reward": float(np.max(recent_rewards)) if recent_rewards else 0.0,
            "min_recent_reward": float(np.min(recent_rewards)) if recent_rewards else 0.0,
            "mean_all_reward": float(np.mean(self.live_rewards)),
        }

    def detect_drift(self, threshold: float = -0.10) -> bool:
        """
        Detect performance degradation (drift).
        
        Args:
            threshold: Threshold for acceptable performance change (-10% by default)
            
        Returns:
            True if drift detected, False otherwise
        """
        if len(self.live_rewards) < 200:
            return False  # Not enough data
        
        old_perf = np.mean(self.live_rewards[-200:-100])
        new_perf = np.mean(self.live_rewards[-100:])
        
        pct_change = (new_perf - old_perf) / (abs(old_perf) + 1e-6)
        
        if pct_change < threshold:
            logger.warning(f"Performance drift detected: {pct_change:.2%}")
            return True
        
        return False


class ReplayBuffer:
    """
    Experience replay buffer for off-policy learning.
    
    Features:
    - Prioritized experience samples frequent/recent transitions
    - Memory efficient: circular buffer
    - Supports variable-length episodes
    """

    def __init__(self, capacity: int = 100_000, priority_alpha: float = 0.6):
        """
        Initialize replay buffer.
        
        Args:
            capacity: Maximum buffer size
            priority_alpha: Prioritization strength (0=uniform, 1=full priority)
        """
        self.capacity = capacity
        self.priority_alpha = priority_alpha
        self.buffer: List[Dict] = []
        self.priorities = np.array([], dtype=np.float32)
        self.pos = 0

    def add(self, experience: Dict, priority: float = 1.0):
        """Add experience to buffer."""
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities = np.append(self.priorities, priority)
        else:
            self.buffer[self.pos] = experience
            self.priorities[self.pos] = priority
            self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int) -> List[Dict]:
        """Sample batch with prioritization."""
        if len(self.buffer) == 0:
            return []
        
        # Compute probabilities
        priorities = self.priorities[:len(self.buffer)]
        probabilities = (priorities ** self.priority_alpha) / (priorities ** self.priority_alpha).sum()
        
        # Sample indices
        indices = np.random.choice(len(self.buffer), size=min(batch_size, len(self.buffer)), 
                                  p=probabilities, replace=False)
        
        return [self.buffer[i] for i in indices]

    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()
        self.priorities = np.array([], dtype=np.float32)
        self.pos = 0

    @property
    def size(self) -> int:
        """Current buffer size."""
        return len(self.buffer)
