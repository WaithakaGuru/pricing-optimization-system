"""Phase 2 Alt: SAC (Soft Actor-Critic) agent."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging
from typing import Tuple, Dict, Deque
from collections import deque

logger = logging.getLogger(__name__)


class QNetwork(nn.Module):
    """Q-function network for SAC."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim + action_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
        self.relu = nn.ReLU()
    
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        x = torch.cat([state, action], dim=-1)
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        q = self.fc3(x)
        return q


class GaussianPolicyNetwork(nn.Module):
    """Actor network with Gaussian policy for SAC."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.mean_head = nn.Linear(hidden_dim, action_dim)
        self.log_std_head = nn.Linear(hidden_dim, action_dim)
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()
        
        # Initialize log_std
        torch.nn.init.constant_(self.log_std_head.weight, -0.5)
        torch.nn.init.constant_(self.log_std_head.bias, -0.5)
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.relu(self.fc1(state))
        x = self.relu(self.fc2(x))
        mean = self.mean_head(x)
        log_std = torch.clamp(self.log_std_head(x), -20, 2)
        return mean, log_std
    
    def sample(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        mean, log_std = self.forward(state)
        std = torch.exp(log_std)
        eps = torch.randn_like(mean)
        action = mean + eps * std
        
        # Compute log probability
        log_prob = -0.5 * (((action - mean) ** 2) / (std ** 2) + 2 * log_std + np.log(2 * np.pi))
        log_prob = log_prob.sum(dim=-1, keepdim=True)
        
        # Tanh squashing
        action = torch.tanh(action)
        log_prob = log_prob - torch.sum(torch.log(1 - action.pow(2) + 1e-6), dim=-1, keepdim=True)
        
        return action, log_prob
    
    def get_action(self, state: torch.Tensor, deterministic: bool = False) -> Tuple[torch.Tensor, torch.Tensor]:
        mean, log_std = self.forward(state)
        if deterministic:
            return torch.tanh(mean), None
        std = torch.exp(log_std)
        eps = torch.randn_like(mean)
        action = torch.tanh(mean + eps * std)
        return action, None


class SACAgent:
    """
    SAC (Soft Actor-Critic) - entropy-regularized off-policy RL for continuous control.
    
    **Why SAC?**
    - Off-policy: Can reuse past experience (more sample-efficient)
    - Entropy regularized: Encourages exploration via maximum entropy objective
    - Two Q-networks: Reduces overestimation bias
    - Automatic temperature tuning: Balances exploration vs exploitation
    - Natural for continuous action spaces (smooth prices)
    
    **Algorithm Overview:**
    1. Collect experience (state, action, reward, next_state, done)
    2. Store in replay buffer
    3. Sample mini-batch from buffer
    4. Update Q-networks: Minimize Bellman error with entropy bonus
    5. Update actor: Maximize expected Q-value minus entropy term
    6. Update temperature: Automatic entropy coefficient tuning
    7. Soft update target Q-networks: target ← τ·online + (1-τ)·target
    
    **Key Hyperparameters:**
    - gamma: Discount factor (typically 0.99)
    - tau: Soft update rate (typically 0.005)
    - entropy_target: Target entropy for autotune (typically -action_dim)
    - lr: Learning rate
    - batch_size: Mini-batch size
    - buffer_size: Replay buffer maximum size
    """

    def __init__(
        self,
        state_dim: int = 12,
        action_dim: int = 1,
        hidden_dim: int = 128,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        tau: float = 0.005,
        entropy_coef: float = 0.2,
        entropy_target: float = None,
        batch_size: int = 64,
        buffer_size: int = 100000,
        device: str = "cpu",
    ):
        """
        Initialize SAC agent.
        
        Args:
            state_dim: Dimension of state space (default 12)
            action_dim: Dimension of action space (default 1 for price)
            hidden_dim: Hidden layer size
            learning_rate: Optimizer learning rate
            gamma: Discount factor
            tau: Soft update coefficient (target networks)
            entropy_coef: Initial entropy regularization coefficient
            entropy_target: Target entropy (for auto-tuning). Defaults to -action_dim
            batch_size: Mini-batch size for updates
            buffer_size: Replay buffer maximum size
            device: "cpu" or "cuda"
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.tau = tau
        self.batch_size = batch_size
        self.device = torch.device(device)
        
        # Entropy target (auto-tuning)
        self.entropy_target = entropy_target or -action_dim
        self.log_alpha = torch.zeros(1, requires_grad=True, device=self.device)
        self.alpha = entropy_coef
        self.alpha_optimizer = torch.optim.Adam([self.log_alpha], lr=learning_rate)
        
        # Networks
        self.actor = GaussianPolicyNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        self.q1 = QNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        self.q2 = QNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        
        # Target networks
        self.q1_target = QNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        self.q2_target = QNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        
        # Copy weights to target networks
        self.q1_target.load_state_dict(self.q1.state_dict())
        self.q2_target.load_state_dict(self.q2.state_dict())
        
        # Optimizers
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=learning_rate)
        self.q1_optimizer = torch.optim.Adam(self.q1.parameters(), lr=learning_rate)
        self.q2_optimizer = torch.optim.Adam(self.q2.parameters(), lr=learning_rate)
        
        # Replay buffer
        self.replay_buffer: Deque = deque(maxlen=buffer_size)
        
        logger.info(f"SAC Agent initialized: state_dim={state_dim}, action_dim={action_dim}")

    def select_action(
        self,
        state: np.ndarray,
        deterministic: bool = False,
    ) -> Tuple[np.ndarray, float, float]:
        """
        Select action (price) using current policy.
        
        Args:
            state: State vector
            deterministic: If True, return mean action (no sampling)
        
        Returns:
            action: Continuous price action
            log_prob: Log probability (None if deterministic)
            value: Q-value estimate from first Q-network (for compatibility with PPO interface)
        """
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            
            if deterministic:
                action, _ = self.actor.get_action(state_tensor, deterministic=True)
                log_prob = None
            else:
                action, _ = self.actor.sample(state_tensor)
                log_prob = 0.0
            
            # Estimate value from Q1 network
            q_value = self.q1(state_tensor, action).squeeze().cpu().numpy()
            value = float(q_value) if isinstance(q_value, np.ndarray) else float(q_value)
            
            # Scale action from [-1, 1] to price range [0.1, 1000]
            action = action.squeeze().cpu().numpy()
            action = self._scale_action(action)
            # Convert to Python float
            action = float(action) if isinstance(action, np.ndarray) else float(action)
        
        return action, log_prob, value

    def store_experience(
        self,
        state: np.ndarray,
        action: np.ndarray,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        """Store experience in replay buffer."""
        self.replay_buffer.append((state, action, reward, next_state, done))

    def _scale_action(self, action: np.ndarray) -> np.ndarray:
        """Scale action from [-1, 1] to [0.1, 1000]."""
        return np.clip(action * 500 + 500.05, 0.1, 1000.0)

    def _unscale_action(self, action: np.ndarray) -> np.ndarray:
        """Scale action from [0.1, 1000] to [-1, 1]."""
        return (action - 500.05) / 500.0

    def update(self, n_updates: int = 1):
        """
        Update actor and critics using experience from replay buffer.
        
        Args:
            n_updates: Number of update steps
        """
        if len(self.replay_buffer) < self.batch_size:
            logger.warning("Replay buffer too small for update")
            return
        
        for _ in range(n_updates):
            # Sample batch
            batch_indices = np.random.choice(len(self.replay_buffer), self.batch_size, replace=False)
            batch = [self.replay_buffer[i] for i in batch_indices]
            
            states, actions, rewards, next_states, dones = zip(*batch)
            
            states = torch.FloatTensor(np.array(states)).to(self.device)
            actions = torch.FloatTensor(np.array(actions)).to(self.device).unsqueeze(-1)
            rewards = torch.FloatTensor(np.array(rewards)).to(self.device).unsqueeze(-1)
            next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
            dones = torch.FloatTensor(np.array(dones)).to(self.device).unsqueeze(-1)
            
            # Current alpha (entropy coefficient)
            alpha = self.log_alpha.exp().detach()
            
            # === Update Q-networks ===
            with torch.no_grad():
                next_actions, next_log_probs = self.actor.sample(next_states)
                
                # Double Q-learning: use minimum of two target Q-networks
                q1_target_next = self.q1_target(next_states, next_actions)
                q2_target_next = self.q2_target(next_states, next_actions)
                q_target_next = torch.min(q1_target_next, q2_target_next)
                
                # Entropy-regularized Bellman target
                q_target = rewards + self.gamma * (1 - dones) * (q_target_next - alpha * next_log_probs)
            
            # Q-network losses
            q1_loss = F.mse_loss(self.q1(states, actions), q_target)
            q2_loss = F.mse_loss(self.q2(states, actions), q_target)
            
            self.q1_optimizer.zero_grad()
            q1_loss.backward()
            self.q1_optimizer.step()
            
            self.q2_optimizer.zero_grad()
            q2_loss.backward()
            self.q2_optimizer.step()
            
            # === Update Actor ===
            sampled_actions, log_probs = self.actor.sample(states)
            q1_sampled = self.q1(states, sampled_actions)
            q2_sampled = self.q2(states, sampled_actions)
            q_sampled = torch.min(q1_sampled, q2_sampled)
            
            actor_loss = (alpha * log_probs - q_sampled).mean()
            
            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            self.actor_optimizer.step()
            
            # === Update Temperature (Alpha) ===
            alpha_loss = -(self.log_alpha * (log_probs.detach() + self.entropy_target)).mean()
            
            self.alpha_optimizer.zero_grad()
            alpha_loss.backward()
            self.alpha_optimizer.step()
            
            self.alpha = self.log_alpha.exp().detach().item()
            
            # === Soft Update Target Networks ===
            self._soft_update_target_networks()
        
        logger.info(
            f"SAC Update - Q1 Loss: {q1_loss.item():.4f}, Actor Loss: {actor_loss.item():.4f}, "
            f"Alpha: {self.alpha:.4f}"
        )

    def _soft_update_target_networks(self):
        """Soft update target networks: target ← τ·online + (1-τ)·target."""
        for param, target_param in zip(self.q1.parameters(), self.q1_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
        
        for param, target_param in zip(self.q2.parameters(), self.q2_target.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

    def save_checkpoint(self, path: str):
        """Save agent networks to file."""
        checkpoint = {
            "actor": self.actor.state_dict(),
            "q1": self.q1.state_dict(),
            "q2": self.q2.state_dict(),
            "alpha": self.alpha,
        }
        torch.save(checkpoint, path)
        logger.info(f"Checkpoint saved to {path}")

    def load_checkpoint(self, path: str):
        """Load agent networks from file."""
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint["actor"])
        self.q1.load_state_dict(checkpoint["q1"])
        self.q2.load_state_dict(checkpoint["q2"])
        self.alpha = checkpoint["alpha"]
        logger.info(f"Checkpoint loaded from {path}")
