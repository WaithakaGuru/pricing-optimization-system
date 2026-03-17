"""Value network (critic) for RL agents."""
import torch
import torch.nn as nn
import logging

logger = logging.getLogger(__name__)


class ValueNetwork(nn.Module):
    """
    Critic network for policy gradient methods.
    Maps state -> estimated value (expected return).
    """

    def __init__(self, state_dim: int, hidden_dim: int = 128):
        """
        Initialize value network.
        
        Args:
            state_dim: State vector dimension
            hidden_dim: Hidden layer size
        """
        super().__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
        
        self.relu = nn.ReLU()

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            state: State tensor [batch, state_dim]
            
        Returns:
            Value tensor [batch, 1]
        """
        x = self.relu(self.fc1(state))
        x = self.relu(self.fc2(x))
        value = self.fc3(x)
        return value
