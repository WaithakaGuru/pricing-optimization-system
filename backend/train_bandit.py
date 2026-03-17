"""Training script for Phase 1: Contextual Bandit."""
import numpy as np
from rl.agents.bandit import ContextualBandit
from rl.environment.price_env import PriceOptimizationEnv
from utils.synthetic_data import load_synthetic_data_into_db
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("CONTEXTUAL BANDIT TRAINING (Phase 1)")
print("=" * 70)

# Load synthetic data
print("\n📥 Loading synthetic data...")
try:
    load_synthetic_data_into_db()
    print("✅ Data loaded\n")
except Exception as e:
    print(f"⚠️  {e}\n")

# Create environment and bandit
print("🎮 Initializing environment and bandit...")
env = PriceOptimizationEnv(
    product_id="PROD-001",
    config={
        "price_min": 5.0,
        "price_max": 50.0,
        "revenue_weight": 1.0,
        "inventory_weight": 0.5,
        "margin_weight": 0.3,
        "stability_weight": 0.2,
    }
)

bandit = ContextualBandit(
    n_arms=10,  # 10 discrete prices from $5 to $50
    algorithm="ucb",  # Use Upper Confidence Bound
    price_min=5.0,
    price_max=50.0,
)

print(f"✅ Environment ready")
print(f"✅ Bandit ready (Algorithm: {bandit.algorithm}, Arms: {bandit.n_arms})")
print(f"   Prices to try: {[f'${p:.2f}' for p in bandit.prices]}\n")

# Training loop
print("=" * 70)
print("TRAINING LOOP (100 episodes)")
print("=" * 70)

episode_rewards = []
episode_prices = []

for episode in range(100):
    state, info = env.reset()
    episode_reward = 0.0
    episode_price = None
    
    # Run one episode (multiple steps)
    for step in range(5):  # 5 steps per episode
        # Bandit selects arm (price)
        arm = bandit.select_arm(state, epsilon=0.1)
        price = bandit.prices[arm]
        episode_price = price
        
        # Environment executes action
        action = np.array([price])
        state, reward, done, truncated, info = env.step(action)
        
        # Bandit learns from reward
        bandit.update(arm, reward)
        episode_reward += reward
        
        if done or truncated:
            break
    
    episode_rewards.append(episode_reward)
    episode_prices.append(episode_price)
    
    # Progress logging
    if (episode + 1) % 20 == 0:
        avg_reward = np.mean(episode_rewards[-20:])
        best_arm, best_reward = bandit.get_best_arm()
        print(f"Episode {episode+1:3d}: Avg Reward={avg_reward:+.3f} | "
              f"Best Price=${bandit.prices[best_arm]:.2f} (Reward={best_reward:.3f})")

print("\n" + "=" * 70)
print("TRAINING COMPLETE!")
print("=" * 70)

# Final statistics
stats = bandit.get_statistics()

print(f"\n📊 Final Statistics:")
print(f"   Total pulls: {stats['total_pulls']}")
print(f"   Best price found: ${stats['best_price']:.2f}")
print(f"   Best average reward: {stats['best_reward']:.3f}")
print(f"\n💰 Price Exploration:")

for i, price in enumerate(bandit.prices):
    pulls = stats['arm_counts'][i]
    value = stats['arm_values'][i]
    pct = stats['pull_distribution'][i] * 100
    marker = "⭐" if i == stats['best_arm'] else "  "
    print(f"   {marker} ${price:5.2f}: {pulls:3.0f} pulls ({pct:5.1f}%) | "
          f"Avg Reward={value:+.3f}")

print(f"\n✨ Insights:")
print(f"   - Bandit tried all {bandit.n_arms} prices")
print(f"   - Concentrated pulls on ${stats['best_price']:.2f} (highest reward)")
print(f"   - This is Phase 1: Fast learning without deep RL")
print(f"   - Can now transition to Phase 2 (PPO/SAC) with warm-start")

# Save results
results = {
    "type": "Contextual Bandit (Phase 1)",
    "algorithm": stats['algorithm'],
    "total_episodes": 100,
    "total_pulls": stats['total_pulls'],
    "best_price": stats['best_price'],
    "best_reward": stats['best_reward'],
    "prices": stats['prices'],
    "arm_values": stats['arm_values'],
    "arm_counts": [int(c) for c in stats['arm_counts']],
}

print(f"\n💾 Results saved for further analysis")
print("\n" + "=" * 70)
print("✅ Phase 1 Complete! Ready for Phase 2 (PPO/SAC)")
print("=" * 70)
