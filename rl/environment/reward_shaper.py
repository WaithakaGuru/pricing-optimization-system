"""Reward function design - critical for RL success."""
import logging

logger = logging.getLogger(__name__)


class RewardShaper:
    """
    Designs reward function for pricing optimization.
    
    Rewards should balance:
    - Revenue maximization (target)
    - Margin protection (cost-based floor)
    - Inventory turnover (penalize stagnant stock)
    - Demand stability (avoid erratic pricing)
    
    Reward = revenue_gain - inventory_penalty - stability_penalty + margin_bonus
    """

    def __init__(self, config: dict):
        """
        Initialize reward shaper.
        
        Args:
            config: Weights for different reward components
        """
        self.config = config
        self.revenue_weight = config.get("revenue_weight", 1.0)
        self.inventory_weight = config.get("inventory_weight", 0.5)
        self.margin_weight = config.get("margin_weight", 0.3)
        self.stability_weight = config.get("stability_weight", 0.2)

    def compute_reward(self, state: dict, action: float, next_state: dict) -> float:
        """
        Compute reward after price action and demand observation.
        
        Args:
            state: Previous state
            action: Price set
            next_state: Result state (inventory, sales, etc)
            
        Returns:
            Scalar reward
        """
        # TODO: Compute revenue reward
        # TODO: Compute inventory penalty
        # TODO: Compute margin bonus
        # TODO: Combine with weights
        reward = 0.0
        return reward
