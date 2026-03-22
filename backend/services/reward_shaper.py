"""Reward shaper for RL agent training on pricing tasks."""
import logging
import numpy as np
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RewardShaper:
    """
    Computes rewards for RL pricing agent based on transaction outcomes.
    
    **Reward Components:**
    - Revenue: quantity × price (normalized by inventory)
    - Profit: revenue relative to cost
    - Inventory management: penalize stockouts, overstock
    - Demand fulfillment: penalize unmet demand
    - Learning bonus: reward exploration
    
    **Output:** Single scalar reward [-1, 1] for agent update
    """

    def __init__(
        self,
        revenue_weight: float = 0.5,
        profit_weight: float = 0.3,
        inventory_weight: float = 0.1,
        demand_weight: float = 0.1,
    ):
        """
        Initialize reward shaper.
        
        Args:
            revenue_weight: Weight for revenue component
            profit_weight: Weight for profit component
            inventory_weight: Weight for inventory management
            demand_weight: Weight for demand fulfillment
        """
        self.revenue_weight = revenue_weight
        self.profit_weight = profit_weight
        self.inventory_weight = inventory_weight
        self.demand_weight = demand_weight

    def compute_reward(
        self,
        prev_state: Optional[np.ndarray] = None,
        action: float = 0.0,
        curr_state: Optional[np.ndarray] = None,
        transaction: Optional[Dict] = None,
    ) -> float:
        """
        Compute scalar reward for a transaction.
        
        Args:
            prev_state: State vector before action [12-dim]
            action: Price applied (0-200)
            curr_state: State vector after action [12-dim]
            transaction: Transaction details dict
        
        Returns:
            Reward scalar in range [-1, 1]
        """
        if transaction is None:
            transaction = {}
        
        reward = 0.0
        
        # 1. Revenue component: quantity × price
        quantity = transaction.get("quantity", 0)
        price = action
        
        if quantity > 0:
            # Reward increases with revenue, normalized
            revenue = quantity * price
            max_possible_revenue = 20 * 200  # Max quantity × max price
            revenue_norm = min(revenue / max_possible_revenue, 1.0)
            revenue_reward = self.revenue_weight * revenue_norm
            reward += revenue_reward
        
        # 2. Profit component (if cost available)
        cost = transaction.get("cost_per_unit", 50.0)
        if quantity > 0 and cost > 0:
            profit_per_unit = price - cost
            # Reward positive profit, penalize losses
            if profit_per_unit > 0:
                profit_margin = min(profit_per_unit / cost, 1.0)
                profit_reward = self.profit_weight * profit_margin
                reward += profit_reward
            else:
                # Loss penalty
                loss_penalty = self.profit_weight * min(abs(profit_per_unit) / cost, 1.0)
                reward -= loss_penalty
        
        # 3. Inventory management (if state available)
        if curr_state is not None and len(curr_state) >= 3:
            # curr_state[2] is typically normalized inventory [0, 1]
            inventory_level = curr_state[2] if isinstance(curr_state, np.ndarray) else curr_state[2]  #normalized [0,1]
            
            # Reward balanced inventory (not too low, not too high)
            # Optimal: 0.5 (50% of capacity)
            inventory_penalty_low = 0.0
            inventory_penalty_high = 0.0
            
            if inventory_level < 0.1:
                # Stockout risk
                inventory_penalty_low = 0.2
                reward -= self.inventory_weight * inventory_penalty_low
            elif inventory_level > 0.9:
                # Overstock risk
                inventory_penalty_high = 0.15
                reward -= self.inventory_weight * inventory_penalty_high
            else:
                # Healthy inventory level
                dist_from_optimal = abs(inventory_level - 0.5) / 0.5
                inventory_bonus = (1 - dist_from_optimal) * 0.1
                reward += self.inventory_weight * inventory_bonus
        
        # 4. Demand fulfillment (based on quantity sold)
        if quantity > 0:
            # Reward for selling (fulfilling demand)
            demand_bonus = self.demand_weight * min(quantity / 10.0, 1.0)  # 10 units = max bonus
            reward += demand_bonus
        else:
            # No sale = lost opportunity
            demand_penalty = self.demand_weight * 0.3
            reward -= demand_penalty
        
        # Clip reward to [-1, 1]
        reward = np.clip(reward, -1.0, 1.0)
        
        logger.debug(
            f"Reward computed: {reward:.3f} "
            f"(qty={quantity}, price={price:.2f}, inventory={inventory_level if curr_state is not None else 'N/A'})"
        )
        
        return float(reward)

    def compute_batch_rewards(
        self,
        transactions: list,
        states: np.ndarray,
    ) -> np.ndarray:
        """
        Compute rewards for multiple transactions efficiently.
        
        Args:
            transactions: List of transaction dicts
            states: Array of state vectors [N, 12]
        
        Returns:
            Array of rewards [N]
        """
        rewards = []
        for i, txn in enumerate(transactions):
            state = states[i] if i < len(states) else None
            reward = self.compute_reward(
                prev_state=None,
                action=txn.get("price", 0.0),
                curr_state=state,
                transaction=txn,
            )
            rewards.append(reward)
        
        return np.array(rewards)

    def get_config(self) -> Dict:
        """Get current reward shaper configuration."""
        return {
            "revenue_weight": self.revenue_weight,
            "profit_weight": self.profit_weight,
            "inventory_weight": self.inventory_weight,
            "demand_weight": self.demand_weight,
        }

    def set_config(self, config: Dict):
        """Update reward shaper configuration."""
        self.revenue_weight = config.get("revenue_weight", self.revenue_weight)
        self.profit_weight = config.get("profit_weight", self.profit_weight)
        self.inventory_weight = config.get("inventory_weight", self.inventory_weight)
        self.demand_weight = config.get("demand_weight", self.demand_weight)
        
        logger.info(f"RewardShaper config updated: {self.get_config()}")
