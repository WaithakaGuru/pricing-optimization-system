"""Phase 1: Contextual bandit agent."""
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ContextualBandit:
    """
    Contextual bandit for initial price exploration.
    
    Uses UCB (Upper Confidence Bound) or Thompson sampling to balance
    exploration vs exploitation without requiring full RL training.
    """

    def __init__(self, n_arms: int, n_features: int, algorithm: str = "ucb"):
        """
        Initialize contextual bandit.
        
        Args:
            n_arms: Number of price actions (discrete price points)
            n_features: Dimension of context (weather, trends, etc)
            algorithm: 'ucb' or 'thompson'
        """
        self.n_arms = n_arms
        self.n_features = n_features
        self.algorithm = algorithm
        self.counts = np.zeros(n_arms)  # Pull counts per arm
        self.values = np.zeros(n_arms)  # Estimated value per arm
        
    def select_arm(self, context: np.ndarray) -> int:
        """Select arm (price action) given context."""
        # TODO: Implement UCB or Thompson sampling
        pass

    def update(self, arm: int, reward: float):
        """Update estimates after observing reward."""
        # TODO: Update counts and value estimates
        pass
