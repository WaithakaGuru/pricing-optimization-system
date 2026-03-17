"""Reward function design - critical for RL success."""
import logging
import numpy as np

logger = logging.getLogger(__name__)


class RewardShaper:
    """
    Designs reward function for pricing optimization.
    
    **CRITICAL**: The reward function teaches the RL agent what outcomes we want.
    Poor reward design = poor learned behavior.
    
    We balance 4 objectives:
    1. Revenue maximization: Higher price * demand = more revenue
    2. Margin protection: Ensure profit margin stays above cost
    3. Inventory turnover: Penalize slow-moving stock
    4. Price stability: Avoid erratic price changes that confuse customers
    
    Final Reward = revenue_reward - inventory_penalty - stability_penalty + margin_bonus
    
    Rewards are normalized to [-1, 1] range for numerical stability.
    """

    def __init__(self, config: dict = None):
        """
        Initialize reward shaper with configurable weights.
        
        Args:
            config: Dict with keys:
                - revenue_weight: Multiply revenue component (default: 1.0)
                - inventory_weight: Multiply inventory penalty (default: 0.5)
                - margin_weight: Multiply margin bonus (default: 0.3)
                - stability_weight: Multiply price stability penalty (default: 0.2)
                - min_margin_pct: Minimum margin % to maintain (default: 20%)
                - max_inventory_days: Max days worth of inventory to hold (default: 30)
                - max_price_change_pct: Max allowed price change % (default: 10%)
        """
        self.config = config or {}
        
        # Component weights (control how much each objective matters)
        self.revenue_weight = self.config.get("revenue_weight", 1.0)
        self.inventory_weight = self.config.get("inventory_weight", 0.5)
        self.margin_weight = self.config.get("margin_weight", 0.3)
        self.stability_weight = self.config.get("stability_weight", 0.2)
        
        # Boundaries and thresholds
        self.min_margin_pct = self.config.get("min_margin_pct", 20.0)  # Floor margin %
        self.max_inventory_days = self.config.get("max_inventory_days", 30)  # Target inventory
        self.max_price_change_pct = self.config.get("max_price_change_pct", 10.0)  # Price change limit
        
        # For debugging
        self.last_reward_breakdown = {}

    def compute_reward(
        self,
        state: dict,
        action: float,
        next_state: dict,
        debug: bool = False
    ) -> float:
        """
        Compute reward after price action and observing outcomes.
        
        Args:
            state: Previous state dict with keys:
                - product_id, current_price, cost_price, inventory_level
            action: New price set (continuous)
            next_state: Result state dict with keys:
                - quantity_sold, inventory_level, cost_price, current_price
            debug: If True, store detailed reward breakdown
            
        Returns:
            Reward scalar in range [-1, 1]
        """
        try:
            # Extract data
            old_price = state.get("current_price", 1.0)
            cost_price = state.get("cost_price", 0.5)
            old_inventory = state.get("inventory_level", 100)
            
            new_price = action  # Price we set
            quantity_sold = next_state.get("quantity_sold", 0)
            new_inventory = next_state.get("inventory_level", old_inventory)
            
            # Compute individual reward components
            revenue_reward = self._compute_revenue_reward(old_price, new_price, quantity_sold, cost_price)
            margin_bonus = self._compute_margin_bonus(new_price, cost_price)
            inventory_penalty = self._compute_inventory_penalty(new_inventory, quantity_sold, cost_price)
            stability_penalty = self._compute_stability_penalty(old_price, new_price)
            
            # Combine components
            total_reward = (
                self.revenue_weight * revenue_reward
                + self.margin_weight * margin_bonus
                - self.inventory_weight * inventory_penalty
                - self.stability_weight * stability_penalty
            )
            
            # Normalize to [-1, 1]
            total_reward = np.clip(total_reward, -1.0, 1.0)
            
            # Store breakdown for debugging
            if debug:
                self.last_reward_breakdown = {
                    "revenue_reward": revenue_reward,
                    "margin_bonus": margin_bonus,
                    "inventory_penalty": inventory_penalty,
                    "stability_penalty": stability_penalty,
                    "total_reward": total_reward,
                }
            
            return float(total_reward)
            
        except Exception as e:
            logger.error(f"Error computing reward: {e}")
            return 0.0

    def _compute_revenue_reward(
        self,
        old_price: float,
        new_price: float,
        quantity_sold: float,
        cost_price: float
    ) -> float:
        """
        Compute revenue reward component.
        
        Reward = (revenue_at_new_price - revenue_at_old_price) / revenue_at_old_price
        
        Normalized to [-1, 1].
        """
        if old_price <= 0 or cost_price <= 0:
            return 0.0
        
        # Current revenue baseline (assume quantity sold at old price)
        baseline_revenue = old_price * quantity_sold - cost_price * quantity_sold
        
        # Revenue at new price (assume same quantity, simplified)
        new_revenue = new_price * quantity_sold - cost_price * quantity_sold
        
        if baseline_revenue == 0:
            return 0.5 if new_revenue > 0 else -0.5
        
        # Percentage change in profit
        pct_change = (new_revenue - baseline_revenue) / abs(baseline_revenue)
        
        # Normalize to [-1, 1]
        reward = np.tanh(pct_change)  # tanh squashes to [-1, 1]
        
        return float(reward)

    def _compute_margin_bonus(self, new_price: float, cost_price: float) -> float:
        """
        Compute margin bonus.
        
        Reward if we maintain healthy margin. Penalize if below minimum.
        """
        if new_price <= 0 or cost_price <= 0:
            return -1.0
        
        margin_pct = ((new_price - cost_price) / new_price) * 100
        
        if margin_pct >= self.min_margin_pct:
            # Good: margin above threshold
            # Reward more for higher margins
            excess_margin = margin_pct - self.min_margin_pct
            return min(1.0, excess_margin / 50.0)  # Max bonus at 70% margin
        else:
            # Bad: margin below threshold
            return -1.0 + (margin_pct / self.min_margin_pct)

    def _compute_inventory_penalty(
        self,
        inventory_level: float,
        quantity_sold: float,
        cost_price: float
    ) -> float:
        """
        Compute inventory penalty.
        
        Penalize high inventory (excess capital tied up) and slow turnover.
        
        Penalty = inventory_cost / max_inventory_cost
        """
        if quantity_sold <= 0:
            # No sales = maximum penalty
            return 1.0
        
        # Days of inventory remaining
        days_of_inventory = inventory_level / max(quantity_sold, 0.1)
        
        if days_of_inventory <= self.max_inventory_days:
            # Good: inventory within acceptable range
            return days_of_inventory / self.max_inventory_days * 0.3  # Small penalty
        else:
            # Bad: excess inventory
            excess_days = days_of_inventory - self.max_inventory_days
            penalty = min(1.0, excess_days / self.max_inventory_days)
            return penalty

    def _compute_stability_penalty(self, old_price: float, new_price: float) -> float:
        """
        Compute price stability penalty.
        
        Penalize large price swings to avoid confusing customers.
        Smooth pricing is better for customer trust.
        """
        if old_price <= 0:
            return 0.0
        
        pct_change = abs((new_price - old_price) / old_price) * 100
        
        if pct_change <= self.max_price_change_pct:
            # Good: reasonable price change
            return pct_change / self.max_price_change_pct * 0.3  # Small penalty
        else:
            # Bad: erratic pricing
            excess_change = pct_change - self.max_price_change_pct
            penalty = min(1.0, excess_change / self.max_price_change_pct)
            return penalty

    def get_reward_breakdown(self) -> dict:
        """Return the last detailed reward breakdown (for debugging/monitoring)."""
        return self.last_reward_breakdown
