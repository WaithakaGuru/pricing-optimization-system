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
        revenue_weight: float = 0.4,
        profit_weight: float = 0.25,
        inventory_weight: float = 0.15,
        demand_weight: float = 0.1,
        price_sanity_weight: float = 0.1,
        min_price: float = 0.1,
        max_price: float = 1000.0,
    ):
        """
        Initialize reward shaper.
        
        Args:
            revenue_weight: Weight for revenue component (0.4)
            profit_weight: Weight for profit component (0.25)
            inventory_weight: Weight for inventory management (0.15)
            demand_weight: Weight for demand fulfillment (0.1)
            price_sanity_weight: Weight for price sanity checks (0.1)
            min_price: Product minimum price (product-aware)
            max_price: Product maximum price (product-aware)
        
        Note: Weights sum to 1.0 to prevent reward saturation. Allows agents to 
        learn proper price discrimination instead of always achieving ~1.0 reward.
        """
        self.revenue_weight = revenue_weight
        self.profit_weight = profit_weight
        self.inventory_weight = inventory_weight
        self.demand_weight = demand_weight
        self.price_sanity_weight = price_sanity_weight
        self.min_price = min_price
        self.max_price = max_price

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
        
        # NOTE: We reward PROFIT, not raw revenue!
        # Raw revenue reward causes agents to maximize price (ignoring quantity/demand).
        # Instead, we should reward profitable transactions.
        if quantity > 0:
            # Revenue component is PROFIT-based, not price-based
            # This prevents agents from gaming the system by raising prices infinitely
            cost_per_unit = transaction.get("cost_per_unit", 50.0)
            profit = quantity * (price - cost_per_unit)
            max_possible_profit = 20 * 150  # Max qty × max profit per unit
            profit_norm = min(profit / max_possible_profit, 1.0) if max_possible_profit > 0 else 0
            revenue_reward = self.revenue_weight * profit_norm
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
        
        # 5. PRICE SANITY CHECK - Prevent extreme pricing strategies
        # Get current price from state if available
        current_price = 50.0  # Default fallback
        if prev_state is not None and len(prev_state) > 0:
            # prev_state[0] is typically normalized current_price
            current_price = float(prev_state[0]) * 900 + 0.1 if isinstance(prev_state[0], (int, float)) else 50.0
        
        # CRITICAL: Penalize prices that deviate far from current price
        # Reasonable pricing <= 15% change from current price
        # Excessive pricing (> 30% change) gets heavy penalty
        
        price_change_pct = (action - current_price) / current_price if current_price > 0 else 0
        
        if price_change_pct > 0.30:
            # More than 30% markup is unreasonable
            # HEAVY penalty: 0.3 - 0.5 reward points
            excessive_markup_penalty = min((price_change_pct - 0.30) / 0.40, 1.0)  # Scale 30-70% range
            price_sanity_penalty = 0.3 * excessive_markup_penalty  # 0-0.3 penalty
            reward -= price_sanity_penalty
            logger.debug(f"Excessive markup penalty: -{price_sanity_penalty:.3f} "
                        f"({price_change_pct*100:.1f}% change, price {action:.2f} vs current {current_price:.2f})")
        elif price_change_pct > 0.15:
            # 15-30% markup is moderate
            # Light penalty: 0.05 - 0.1 reward points
            moderate_markup_penalty = (price_change_pct - 0.15) / 0.15  # 0-1 range for 15-30%
            price_sanity_penalty = 0.1 * moderate_markup_penalty
            reward -= price_sanity_penalty
            logger.debug(f"Moderate markup penalty: -{price_sanity_penalty:.3f} "
                        f"({price_change_pct*100:.1f}% change)")
        
        if price_change_pct < -0.20:
            # More than 20% discount is risky
            excessive_discount_penalty = min(abs(price_change_pct + 0.20) / 0.30, 1.0)
            price_sanity_penalty = 0.2 * excessive_discount_penalty  # 0-0.2 penalty
            reward -= price_sanity_penalty
            logger.debug(f"Excessive discount penalty: -{price_sanity_penalty:.3f} ({price_change_pct*100:.1f}% change)")
        
        # Penalize prices below cost recovery
        cost_per_unit = transaction.get("cost_per_unit", 0.0)
        if cost_per_unit > 0 and action < cost_per_unit * 0.95:
            # Price below 95% of cost = significant loss
            loss_penalty = 0.3  # HEAVY penalty for losses
            reward -= loss_penalty
            logger.debug(f"Unsafe low price penalty: -{loss_penalty:.3f} (price {action:.2f} vs cost {cost_per_unit:.2f})")
        elif cost_per_unit > 0 and action < cost_per_unit:
            # Price below cost = emergency situation
            emergency_loss_penalty = 0.5  # VERY HEAVY penalty
            reward -= emergency_loss_penalty
            logger.debug(f"CRITICAL LOSS penalty: -{emergency_loss_penalty:.3f} (price {action:.2f} vs cost {cost_per_unit:.2f})")
        
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
            "price_sanity_weight": self.price_sanity_weight,
            "min_price": self.min_price,
            "max_price": self.max_price,
        }

    def set_config(self, config: Dict):
        """Update reward shaper configuration."""
        self.revenue_weight = config.get("revenue_weight", self.revenue_weight)
        self.profit_weight = config.get("profit_weight", self.profit_weight)
        self.inventory_weight = config.get("inventory_weight", self.inventory_weight)
        self.demand_weight = config.get("demand_weight", self.demand_weight)
        self.price_sanity_weight = config.get("price_sanity_weight", self.price_sanity_weight)
        self.min_price = config.get("min_price", self.min_price)
        self.max_price = config.get("max_price", self.max_price)
        
        logger.info(f"RewardShaper config updated: {self.get_config()}")
