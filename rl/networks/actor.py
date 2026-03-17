"""Policy network (actor) for RL agents."""
import torch
import torch.nn as nn
import logging

logger = logging.getLogger(__name__)


class PolicyNetwork(nn.Module):
    """
    Actor network for policy gradient methods (PPO, SAC).
    Maps state -> action distribution.
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        """
        Initialize policy network.
        
        Args:
            state_dim: State vector dimension
            action_dim: Action vector dimension
            hidden_dim: Hidden layer size
        """
        super().__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)
        
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()  # For continuous action bounds

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            state: State tensor [batch, state_dim]
            
        Returns:
            Action tensor [batch, action_dim]
        """
        x = self.relu(self.fc1(state))
        x = self.relu(self.fc2(x))
        action = self.tanh(self.fc3(x))  # Bounded to [-1, 1]
        return action
