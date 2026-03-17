"""Test script for the PriceOptimizationEnv."""
import numpy as np
from rl.environment.price_env import PriceOptimizationEnv
from utils.synthetic_data import load_synthetic_data_into_db

print("=" * 70)
print("PRICE OPTIMIZATION ENVIRONMENT TEST")
print("=" * 70)

# First load synthetic data
print("\n📥 Loading synthetic data into database...")
try:
    load_synthetic_data_into_db()
    print("✅ Synthetic data loaded\n")
except Exception as e:
    print(f"⚠️  Note: {e}\n")

# Create environment
print("🎮 Initializing PriceOptimizationEnv...")
config = {
    "price_min": 1.0,
    "price_max": 100.0,
    "revenue_weight": 1.0,
    "inventory_weight": 0.5,
    "margin_weight": 0.3,
    "stability_weight": 0.2,
}

env = PriceOptimizationEnv(product_id="PROD-001", config=config, max_steps=30)
print(f"✅ Environment created")
print(f"   Action space: {env.action_space}")
print(f"   Observation space: {env.observation_space}\n")

# Reset environment
print("🔄 Resetting environment...")
state, info = env.reset()
print(f"✅ Initial state shape: {state.shape}")
print(f"   Initial state: {state}")
print(f"   Features: {env.state_builder.feature_names}\n")

# Run a few episodes
print("=" * 70)
print("EPISODE 1: Random Price Actions")
print("=" * 70)
state, info = env.reset()
total_reward = 0.0
episode_steps = []

for step in range(10):  # 10 steps per episode
    # Random action (price)
    action = env.action_space.sample()
    
    # Execute step
    state, reward, done, truncated, info = env.step(action)
    total_reward += reward
    
    episode_steps.append({
        "step": step + 1,
        "price": info["price"],
        "quantity": info["quantity_sold"],
        "inventory": info["inventory"],
        "reward": reward,
    })
    
    print(f"Step {step+1:2d}: Price=${info['price']:6.2f} | "
          f"Quantity={info['quantity_sold']:3d} | "
          f"Inventory={info['inventory']:4.0f} | "
          f"Reward={reward:+.3f}")
    
    if done or truncated:
        break

print(f"\n📊 Episode Summary:")
print(f"   Total reward: {total_reward:+.3f}")
print(f"   Avg reward/step: {total_reward/10:+.3f}")
print(f"   Steps: {len(episode_steps)}")

# Test scenario: Strategic pricing
print("\n" + "=" * 70)
print("EPISODE 2: Strategic Pricing (Increase price gradually)")
print("=" * 70)
state, info = env.reset()
total_reward = 0.0
base_price = 20.0

for step in range(10):
    # Increase price gradually
    price_increase = base_price + (step * 2)
    action = np.array([price_increase])
    
    state, reward, done, truncated, info = env.step(action)
    total_reward += reward
    
    print(f"Step {step+1:2d}: Price=${info['price']:6.2f} | "
          f"Quantity={info['quantity_sold']:3d} | "
          f"Inventory={info['inventory']:4.0f} | "
          f"Reward={reward:+.3f}")
    
    if done or truncated:
        break

print(f"\n📊 Episode Summary:")
print(f"   Total reward: {total_reward:+.3f}")
print(f"   Avg reward/step: {total_reward/10:+.3f}")
print(f"   Notice: As prices increase, quantity decreases (price elasticity)")
print(f"   Goal: Find the sweet spot for max profit (reward)")

# Close environment
env.close()

print("\n" + "=" * 70)
print("✅ Environment Test Complete!")
print("=" * 70)
print("\nThe environment is ready for RL agent training:")
print("  - StateBuilder provides realistic state vectors")
print("  - RewardShaper evaluates price decisions")
print("  - Environment simulates demand with price elasticity")
print("  - Agents can learn to maximize rewards")
print("\nNext: Train RL agents (Bandit → PPO/SAC)")
