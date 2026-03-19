"""Phase 2: PPO (Proximal Policy Optimization) agent."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging
from typing import Tuple, Dict, List
from rl.networks.actor import PolicyNetwork
from rl.networks.critic import ValueNetwork

logger = logging.getLogger(__name__)


class PPOAgent:
    """
    PPO (Proximal Policy Optimization) agent for dynamic pricing.
    
    **Why PPO?**
    - Stable policy gradient method with clipping to prevent large updates
    - Sample-efficient: reuses experience multiple times
    - Better stability than vanilla PG methods
    - Natural fit for continuous price actions
    
    **Algorithm Overview:**
    1. Collect experience (state, action, reward, log_prob, value)
    2. Compute advantages: A = reward - V(state)
    3. Update policy: maximize surrogate objective with clipping
    4. Update value function: minimize MSE loss
    5. Repeat
    
    **Key Hyperparameters:**
    - clip_ratio: PPO clipping range (typically 0.2)
    - entropy_coef: Entropy bonus to encourage exploration
    - lr: Learning rate for policy/value updates
    - gamma: Discount factor for future rewards
    - gae_lambda: Lambda for Generalized Advantage Estimation
    """

    def __init__(
        self,
        state_dim: int = 12,
        action_dim: int = 1,
        hidden_dim: int = 128,
        learning_rate: float = 3e-4,
        clip_ratio: float = 0.2,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        batch_size: int = 64,
        n_epochs: int = 10,
        device: str = "cpu",
    ):
        """
        Initialize PPO agent.
        
        Args:
            state_dim: Dimension of state space (default 12 from StateBuilder)
            action_dim: Dimension of action space (default 1 for price)
            hidden_dim: Hidden layer size
            learning_rate: Optimizer learning rate
            clip_ratio: PPO clipping epsilon (typically 0.1-0.3)
            entropy_coef: Coefficient for entropy regularization
            value_coef: Coefficient for value function loss
            gamma: Discount factor
            gae_lambda: Lambda for GAE computation
            batch_size: Mini-batch size for updates
            n_epochs: Number of epochs to train per update
            device: "cpu" or "cuda"
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        self.clip_ratio = clip_ratio
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.batch_size = batch_size
        self.n_epochs = n_epochs
        self.device = torch.device(device)
        
        # Initialize networks
        self.actor = PolicyNetwork(state_dim, action_dim, hidden_dim).to(self.device)
        self.critic = ValueNetwork(state_dim, hidden_dim).to(self.device)
        
        # Optimizers
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=learning_rate)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=learning_rate)
        
        # Experience buffer
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
        
        logger.info(f"PPO Agent initialized with state_dim={state_dim}, action_dim={action_dim}")

    def select_action(
        self,
        state: np.ndarray,
        deterministic: bool = False,
    ) -> Tuple[np.ndarray, float, float]:
        """
        Select action (price) given state using current policy.
        
        Args:
            state: State vector (shape: state_dim,)
            deterministic: If True, use mean action (no sampling)
        
        Returns:
            action: Selected price action
            log_prob: Log probability of action (float)
            value: Estimated state value (float)
        """
        with torch.no_grad():
            # Convert state to tensor
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            
            # Get action from actor
            action_mean = self.actor(state_tensor)
            
            # Get value from critic
            value = self.critic(state_tensor).squeeze().cpu().numpy()
            if isinstance(value, np.ndarray):
                value = float(value)
            else:
                value = float(value)
            
            if deterministic:
                action = action_mean.squeeze().cpu().numpy()
                log_prob = 0.0
            else:
                # Add exploration noise (Gaussian)
                noise = torch.randn_like(action_mean) * 0.1
                action = action_mean + noise
                
                # Compute log probability (approximate as Gaussian)
                log_prob_tensor = -0.5 * (noise ** 2).sum()
                log_prob = float(log_prob_tensor.cpu().numpy())
            
            # Scale action from network output to price range [0.1, 1000]
            # Network outputs in [-1, 1] from tanh
            action_scaled = action.squeeze().cpu().numpy()
            action_scaled = float(action_scaled) if isinstance(action_scaled, np.ndarray) else action_scaled
            # Scale from [-1, 1] to [0.1, 1000]
            action_scaled = (action_scaled + 1.0) / 2.0 * 999.9 + 0.1
            action_scaled = np.clip(action_scaled, 0.1, 1000.0)
        
        return action_scaled, log_prob, value

    def store_experience(
        self,
        state: np.ndarray,
        action: np.ndarray,
        reward: float,
        log_prob: float,
        value: float,
        done: bool,
    ):
        """Store experience in buffer."""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.dones.append(done)

    def _compute_advantages(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute advantages and returns using Generalized Advantage Estimation (GAE).
        
        GAE provides a trade-off between bias (1-step) and variance (n-step).
        
        Returns:
            advantages: Advantage estimates
            returns: Discounted return estimates
        """
        n = len(self.rewards)
        advantages = np.zeros(n)
        returns = np.zeros(n)
        
        # Last value (0 if done, otherwise use critic estimate)
        next_value = 0.0
        gae = 0.0
        
        for t in reversed(range(n)):
            if t == n - 1:
                next_value = 0.0 if self.dones[t] else 0.0
            else:
                next_value = self.values[t + 1]
            
            # TD error
            td_error = self.rewards[t] + self.gamma * next_value - self.values[t]
            
            # GAE accumulation
            gae = td_error + self.gamma * self.gae_lambda * (1 - self.dones[t]) * gae
            advantages[t] = gae
            returns[t] = gae + self.values[t]
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        return advantages, returns

    def update(self):
        """
        Update policy and value function using PPO objective.
        
        Performs multiple epochs of mini-batch SGD on collected experience.
        """
        if len(self.states) == 0:
            logger.warning("No experience to update from")
            return
        
        # Compute advantages and returns
        advantages, returns = self._compute_advantages()
        
        # Convert to tensors
        states = torch.FloatTensor(np.array(self.states)).to(self.device)
        actions = torch.FloatTensor(np.array(self.actions)).to(self.device)
        log_probs_old = torch.FloatTensor(np.array(self.log_probs)).to(self.device)
        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = torch.FloatTensor(returns).to(self.device)
        
        n_samples = len(self.states)
        
        # Training loops
        for epoch in range(self.n_epochs):
            # Shuffle indices
            indices = np.random.permutation(n_samples)
            
            for i in range(0, n_samples, self.batch_size):
                batch_indices = indices[i:i + self.batch_size]
                
                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_log_probs_old = log_probs_old[batch_indices]
                batch_advantages = advantages[batch_indices]
                batch_returns = returns[batch_indices]
                
                # Actor update (policy gradient with PPO clipping)
                action_pred = self.actor(batch_states)
                
                # Reshape batch_actions to match action_pred shape [batch, 1]
                if batch_actions.dim() == 1:
                    batch_actions = batch_actions.unsqueeze(-1)
                
                # Approximate log prob with MSE loss between actions
                log_probs_new = -F.mse_loss(action_pred, batch_actions, reduction='none').mean(dim=1)
                
                ratio = torch.exp(log_probs_new - batch_log_probs_old)
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_ratio, 1 + self.clip_ratio) * batch_advantages
                
                actor_loss = -torch.min(surr1, surr2).mean()
                
                self.actor_optimizer.zero_grad()
                actor_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.actor.parameters(), max_norm=0.5)
                self.actor_optimizer.step()
                
                # Critic update (value function regression)
                value_pred = self.critic(batch_states).squeeze()
                critic_loss = F.mse_loss(value_pred, batch_returns)
                
                self.critic_optimizer.zero_grad()
                critic_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.critic.parameters(), max_norm=0.5)
                self.critic_optimizer.step()
        
        logger.info(f"PPO Update - Actor Loss: {actor_loss.item():.4f}, Critic Loss: {critic_loss.item():.4f}")
        
        # Clear buffer
        self.clear_buffer()

    def clear_buffer(self):
        """Clear experience buffer."""
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []

    def save_checkpoint(self, path: str):
        """Save agent networks to file."""
        checkpoint = {
            "actor": self.actor.state_dict(),
            "critic": self.critic.state_dict(),
        }
        torch.save(checkpoint, path)
        logger.info(f"Checkpoint saved to {path}")

    def load_checkpoint(self, path: str):
        """Load agent networks from file."""
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint["actor"])
        self.critic.load_state_dict(checkpoint["critic"])
        logger.info(f"Checkpoint loaded from {path}")
