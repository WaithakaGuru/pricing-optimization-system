"""Gym-compatible price optimization environment."""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import logging
from rl.environment.state_builder import StateBuilder
from rl.environment.reward_shaper import RewardShaper

logger = logging.getLogger(__name__)


class PriceOptimizationEnv(gym.Env):
    """
    Custom Gymnasium environment for dynamic pricing optimization.
    
    This environment simulates a retail scenario where:
    - **State**: [current_price, cost, margin, inventory, demand, trends, weather, ...]
    - **Action**: Set a new price (continuous value)
    - **Reward**: Revenue + margin safety - inventory penalty - price stability penalty
    
    The agent learns to set optimal prices given market conditions.
    
    Example usage:
    ```python
    env = PriceOptimizationEnv(product_id="PROD-001")
    state, info = env.reset()
    
    for step in range(100):
        action = env.action_space.sample()  # Random price
        state, reward, done, truncated, info = env.step(action)
        if done or truncated:
            break
    ```
    """
    
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        product_id: str = "PROD-001",
        config: dict = None,
        db_url: str = "sqlite:///pricing.db",
        max_steps: int = 252,  # ~1 trading year
    ):
        """
        Initialize the pricing environment.
        
        Args:
            product_id: Product to optimize
            config: Configuration dict with weights for reward components
            db_url: Database URL
            max_steps: Maximum steps per episode (default 252 = ~1 year)
        """
        super().__init__()
        
        self.product_id = product_id
        self.db_url = db_url
        self.max_steps = max_steps
        self.current_step = 0
        
        # Initialize state builder and reward shaper
        self.state_builder = StateBuilder(db_url=db_url)
        self.reward_shaper = RewardShaper(config or {})
        
        # Action space: continuous price
        # Default: prices from $0.10 to $1000
        self.price_min = config.get("price_min", 0.1) if config else 0.1
        self.price_max = config.get("price_max", 1000.0) if config else 1000.0
        
        self.action_space = spaces.Box(
            low=np.array([self.price_min], dtype=np.float32),
            high=np.array([self.price_max], dtype=np.float32),
            shape=(1,),
            dtype=np.float32,
        )
        
        # Observation space: 12-dimensional state from StateBuilder
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(12,),  # StateBuilder produces 12 features, normalized to [0, 1]
            dtype=np.float32,
        )
        
        # State tracking
        self.state = None
        self.prev_state = None
        self.prev_action = None

    def reset(self, seed=None):
        """
        Reset the environment to initial state.
        
        Returns:
            (state, info): Initial state and metadata
        """
        super().reset(seed=seed)
        
        self.current_step = 0
        self.state = self.state_builder.build_state(self.product_id)
        
        if self.state is None or len(self.state) == 0:
            # Fallback to default state if product not found
            self.state = np.array([0.5] * 12, dtype=np.float32)
            logger.warning(f"Product {self.product_id} not found, using default state")
        
        self.prev_state = self.state.copy()
        self.prev_action = None
        
        info = {"step": self.current_step, "product_id": self.product_id}
        
        return self.state, info

    def step(self, action):
        """
        Execute one step in the environment.
        
        Args:
            action: Price to set (array [price])
            
        Returns:
            (state, reward, done, truncated, info)
        """
        self.current_step += 1
        
        # Extract price from action (handle both scalar and array)
        if isinstance(action, (list, tuple, np.ndarray)):
            new_price = float(action[0]) if len(action) > 0 else float(action)
        else:
            new_price = float(action)
        new_price = np.clip(new_price, self.price_min, self.price_max)  # Enforce bounds
        
        # Build state dict for reward calculation
        # Use placeholder values for quantities (would come from demand forecast in real scenario)
        prev_state_dict = {
            "current_price": self._denormalize_price(self.prev_state[0]) if self.prev_state is not None else new_price,
            "cost_price": self._denormalize_price(self.prev_state[1]) if self.prev_state is not None else new_price * 0.6,
            "inventory_level": self._denormalize_inventory(self.prev_state[3]) if self.prev_state is not None else 100,
        }
        
        # Simulate demand (simplified: base demand with price elasticity)
        # Real system would use demand forecaster
        elasticity = -0.5
        base_demand = 50.0
        price_ratio = new_price / max(prev_state_dict["current_price"], 0.1)
        predicted_quantity = base_demand * (price_ratio ** elasticity)
        predicted_quantity = max(0, int(predicted_quantity + np.random.normal(0, 5)))
        
        # Build next state dict for reward calculation
        next_state_dict = {
            "quantity_sold": predicted_quantity,
            "inventory_level": max(0, prev_state_dict["inventory_level"] - predicted_quantity),
            "cost_price": prev_state_dict["cost_price"],
            "current_price": new_price,
        }
        
        # Compute reward
        reward = self.reward_shaper.compute_reward(prev_state_dict, new_price, next_state_dict, debug=False)
        
        # Get new state
        self.prev_state = self.state.copy()
        self.state = self.state_builder.build_state(self.product_id)
        if self.state is None or len(self.state) == 0:
            self.state = self.prev_state.copy()
        
        self.prev_action = new_price
        
        # Check termination
        done = False
        truncated = self.current_step >= self.max_steps
        
        info = {
            "step": self.current_step,
            "price": new_price,
            "quantity_sold": predicted_quantity,
            "inventory": next_state_dict["inventory_level"],
            "reward_breakdown": self.reward_shaper.get_reward_breakdown(),
        }
        
        return self.state, float(reward), done, truncated, info

    def _denormalize_price(self, normalized: float) -> float:
        """Convert normalized price [0, 1] back to actual price."""
        return normalized * (self.price_max - self.price_min) + self.price_min

    def _denormalize_inventory(self, normalized: float) -> float:
        """Convert normalized inventory [0, 1] back to actual units."""
        return normalized * 10000  # Assume max inventory 10k units

    def render(self):
        """Render environment state (for visualization/debugging)."""
        if self.prev_action is None:
            return
        
        logger.info(
            f"Step {self.current_step}: "
            f"Price=${self.prev_action:.2f}, "
            f"State={self.state[:3]}..."  # Show first 3 state dims
        )

    def close(self):
        """Clean up resources."""
        pass

