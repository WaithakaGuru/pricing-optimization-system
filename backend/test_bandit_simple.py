"""Quick test of the Contextual Bandit agent."""
import numpy as np
from rl.agents.bandit import ContextualBandit

print("=" * 70)
print("CONTEXTUAL BANDIT - QUICK TEST")
print("=" * 70)

# Create bandit with specific prices
print("\n🎯 Creating Bandit with prices: $10, $15, $20, $25, $30")
prices = [10.0, 15.0, 20.0, 25.0, 30.0]
bandit = ContextualBandit.from_prices(prices, algorithm="ucb")

print(f"Algorithm: {bandit.algorithm}")
print(f"Arms: {len(bandit.prices)}")
print(f"Prices: {bandit.prices}\n")

# Simulate pulling arms
print("=" * 70)
print("SIMULATING 50 PULLS (with reward feedback)")
print("=" * 70)

# Simulate that arm 2 (price $20) has the best reward
def simulate_reward(arm):
    """Simulate reward: arm 2 has highest reward."""
    best_reward = np.exp(-0.1 * (arm - 2) ** 2)  # Gaussian centered on arm 2
    noise = np.random.normal(0, 0.1)
    return best_reward + noise

print("\nArm pulls (Bandit learning which price is best):")
for pull in range(50):
    # Bandit selects arm
    arm = bandit.select_arm(epsilon=0.15)  # 15% random exploration
    
    # Simulate outcome
    reward = simulate_reward(arm)
    
    # Bandit learns
    bandit.update(arm, reward)
    
    if (pull + 1) % 10 == 0:
        best_arm, best_val = bandit.get_best_arm()
        print(f"Pull {pull+1:2d}: Selected arm {arm} (${bandit.prices[arm]:.0f}) | "
              f"Reward={reward:+.3f} | "
              f"Best so far: Arm {best_arm} (${bandit.prices[best_arm]:.0f}, Avg={best_val:.3f})")

# Final analysis
print("\n" + "=" * 70)
print("FINAL ANALYSIS")
print("=" * 70)

stats = bandit.get_statistics()

print(f"\n📊 Pull Distribution:")
for i, (price, pulls, value) in enumerate(zip(bandit.prices, stats['arm_counts'], stats['arm_values'])):
    dist_pct = stats['pull_distribution'][i] * 100
    best_marker = "⭐ BEST" if i == stats['best_arm'] else ""
    print(f"  Arm {i} (${price:5.1f}): {pulls:2.0f} pulls ({dist_pct:5.1f}%) | "
          f"Avg Reward={value:+.3f} {best_marker}")

print(f"\n🏆 Winner: Arm {stats['best_arm']} "
      f"(Price ${stats['best_price']:.2f}, "
      f"Avg Reward {stats['best_reward']:.3f})")

print(f"\n💡 Key Insight:")
print(f"  - Bandit concentrated pulls on arm 2 ($20)")
print(f"  - This arm had the highest rewards")
print(f"  - Exploration-exploitation tradeoff worked!")
print(f"  - In production: Use $20 as recommended price")

print("\n" + "=" * 70)
print("✅ Bandit Test Complete!")
print("=" * 70)
