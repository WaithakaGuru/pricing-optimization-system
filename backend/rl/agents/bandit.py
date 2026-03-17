"""Phase 1: Contextual Bandit Agent for Price Exploration."""
import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class ContextualBandit:
    """
    Contextual Bandit for initial price optimization (Phase 1).
    
    **Why Contextual Bandit?**
    - Fast to learn (no full RL training needed)
    - Balances exploration vs exploitation automatically
    - Works well with limited data
    - Good warm-start before transitioning to PPO/SAC (Phase 2)
    
    **Algorithm**: UCB (Upper Confidence Bound) or Thompson Sampling
    - Maintains estimated reward for each price action
    - Optimistically explores uncertain actions (exploration bonus)
    - Exploits high-reward actions (exploitation)
    
    **Arms**: Discrete price points (e.g., $10, $12, $14, $16, $18...)
    **Context**: Product state (demand, inventory, trends, etc)
    **Reward**: From RewardShaper (revenue, margin, turnover, stability)
    """

    def __init__(
        self,
        n_arms: int = 10,
        n_features: int = 12,
        algorithm: str = "ucb",
        price_min: float = 5.0,
        price_max: float = 50.0,
    ):
        """
        Initialize contextual bandit.
        
        Args:
            n_arms: Number of price actions (discrete price points)
                    Default 10 = $5, $9.44, $13.89, ..., $50
            n_features: Context dimension (from StateBuilder, typically 12)
            algorithm: 'ucb' (Upper Confidence Bound) or 'thompson'
            price_min: Minimum price ($)
            price_max: Maximum price ($)
        """
        self.n_arms = n_arms
        self.n_features = n_features
        self.algorithm = algorithm
        self.price_min = price_min
        self.price_max = price_max
        
        # Action space: Create discrete price points
        self.prices = np.linspace(price_min, price_max, n_arms)
        logger.info(f"Arms (prices): {self.prices}")
        
        # Per-arm statistics
        self.counts = np.zeros(n_arms)  # How many times each arm was pulled
        self.values = np.zeros(n_arms)  # Estimated reward for each arm
        
        # For UCB: track sum of rewards and sum of squares for confidence intervals
        self.sum_rewards = np.zeros(n_arms)
        self.sum_sq_rewards = np.zeros(n_arms)
        
        # Thompson sampling: Beta parameters (success, failure counts)
        # Initialize with weak prior (1, 1)
        self.beta_success = np.ones(n_arms)  # α in Beta(α, β)
        self.beta_failure = np.ones(n_arms)  # β in Beta(α, β)
        
        self.total_pulls = 0
        self.learning_rate = 0.1  # For incremental updates

    def select_arm(self, context: np.ndarray, epsilon: float = 0.1) -> int:
        """
        Select price action given context.
        
        Args:
            context: State vector from StateBuilder (shape: 12)
            epsilon: Exploration rate for epsilon-greedy fallback
            
        Returns:
            Arm index (corresponds to a discrete price)
        """
        if self.algorithm == "ucb":
            return self._ucb_select(epsilon)
        elif self.algorithm == "thompson":
            return self._thompson_select()
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")

    def _ucb_select(self, epsilon: float = 0.1) -> int:
        """
        Select arm using Upper Confidence Bound.
        
        UCB = estimated_value + exploration_bonus
        
        Exploration bonus = sqrt(ln(total_pulls) / arm_pulls)
        
        Arms with more uncertainty get higher exploration bonus.
        """
        if self.total_pulls == 0:
            # First pull: random
            return np.random.randint(self.n_arms)
        
        # Epsilon-greedy: sometimes explore randomly
        if np.random.random() < epsilon:
            return np.random.randint(self.n_arms)
        
        # UCB: optimistic estimate of each arm
        ucb_values = np.zeros(self.n_arms)
        
        for arm in range(self.n_arms):
            if self.counts[arm] == 0:
                # Unvisited arm: infinite bonus (must explore)
                ucb_values[arm] = float('inf')
            else:
                # Estimate + exploration bonus
                avg_reward = self.values[arm]
                exploration_bonus = np.sqrt(np.log(self.total_pulls) / self.counts[arm])
                ucb_values[arm] = avg_reward + exploration_bonus
        
        return np.argmax(ucb_values)

    def _thompson_select(self) -> int:
        """
        Select arm using Thompson Sampling.
        
        Sample from Beta distribution for each arm:
        Sample ~ Beta(α, β)  [where α=successes, β=failures]
        
        Pick arm with highest sample.
        """
        # Sample from posterior for each arm
        samples = np.array([
            np.random.beta(self.beta_success[i], self.beta_failure[i])
            for i in range(self.n_arms)
        ])
        
        return np.argmax(samples)

    def update(self, arm: int, reward: float):
        """
        Update arm statistics after observing reward.
        
        Args:
            arm: Arm that was pulled
            reward: Reward received (from RewardShaper, typically in [-1, 1])
        """
        self.counts[arm] += 1
        self.total_pulls += 1
        
        # Incremental average
        old_value = self.values[arm]
        self.values[arm] = old_value + self.learning_rate * (reward - old_value)
        
        # Track sum of rewards for variance calculation
        self.sum_rewards[arm] += reward
        self.sum_sq_rewards[arm] += reward ** 2
        
        # Update Thompson sampling parameters
        # Treat reward as binary: success if reward > 0, failure otherwise
        if reward > 0:
            self.beta_success[arm] += 1
        else:
            self.beta_failure[arm] += 1
        
        logger.debug(
            f"Arm {arm} (Price=${self.prices[arm]:.2f}): "
            f"Reward={reward:.3f}, Avg={self.values[arm]:.3f}, Pulls={self.counts[arm]}"
        )

    def get_best_arm(self) -> Tuple[int, float]:
        """
        Get the best arm found so far.
        
        Returns:
            (arm_index, average_reward)
        """
        if self.total_pulls == 0:
            return 0, 0.0
        
        best_arm = np.argmax(self.values)
        return best_arm, self.values[best_arm]

    def get_best_price(self) -> float:
        """Get the recommended price (best arm's price)."""
        best_arm, _ = self.get_best_arm()
        return self.prices[best_arm]

    def get_statistics(self) -> dict:
        """Return detailed statistics for analysis."""
        best_arm, best_reward = self.get_best_arm()
        
        # Calculate variance per arm
        variances = []
        for i in range(self.n_arms):
            if self.counts[i] > 1:
                mean = self.values[i]
                var = (self.sum_sq_rewards[i] / self.counts[i]) - mean ** 2
                variances.append(var)
            else:
                variances.append(0.0)
        
        return {
            "algorithm": self.algorithm,
            "total_pulls": self.total_pulls,
            "n_arms": self.n_arms,
            "prices": self.prices.tolist(),
            "arm_counts": self.counts.tolist(),
            "arm_values": self.values.tolist(),
            "arm_variances": variances,
            "best_arm": int(best_arm),
            "best_price": float(self.prices[best_arm]),
            "best_reward": float(best_reward),
            "pull_distribution": (self.counts / self.total_pulls).tolist(),
        }

    @classmethod
    def from_prices(cls, prices: list, algorithm: str = "ucb"):
        """
        Create bandit from explicit price list.
        
        Args:
            prices: List of prices to try
            algorithm: 'ucb' or 'thompson'
            
        Returns:
            ContextualBandit instance
        """
        n_arms = len(prices)
        bandit = cls(n_arms=n_arms, algorithm=algorithm)
        bandit.prices = np.array(prices)
        return bandit

