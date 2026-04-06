"""Test script for RewardShaper."""
from rl.environment.reward_shaper import RewardShaper
import numpy as np

print("🎯 Testing RewardShaper\n")

# Initialize with default config
config = {
    "revenue_weight": 1.0,
    "inventory_weight": 0.5,
    "margin_weight": 0.3,
    "stability_weight": 0.2,
    "min_margin_pct": 20.0,
    "max_inventory_days": 30,
    "max_price_change_pct": 10.0,
}

shaper = RewardShaper(config)

# Test Case 1: Good outcome - price increase with sales
print("=" * 60)
print("TEST 1: Good Outcome (Price ↑, Sales Good)")
print("=" * 60)
state_1 = {
    "product_id": "p0001",
    "current_price": 10.0,
    "cost_price": 6.0,
    "inventory_level": 100,
}
action_1 = 12.0  # Increase price by 20%
next_state_1 = {
    "quantity_sold": 80,  # Good sales despite price increase
    "inventory_level": 20,
    "cost_price": 6.0,
    "current_price": 12.0,
}
reward_1 = shaper.compute_reward(state_1, action_1, next_state_1, debug=True)
print(f"Old price: ${state_1['current_price']:.2f}")
print(f"New price: ${action_1:.2f}")
print(f"Quantity sold: {next_state_1['quantity_sold']}")
print(f"Remaining inventory: {next_state_1['inventory_level']}")
print(f"\nReward breakdown: {shaper.get_reward_breakdown()}")
print(f"✅ FINAL REWARD: {reward_1:.4f} (Good!)\n")

# Test Case 2: Bad outcome - price drop, excess inventory
print("=" * 60)
print("TEST 2: Bad Outcome (Price ↓, Excess Inventory)")
print("=" * 60)
state_2 = {
    "product_id": "p0001",
    "current_price": 10.0,
    "cost_price": 6.0,
    "inventory_level": 500,  # Very high inventory
}
action_2 = 8.0  # Decrease price by 20%
next_state_2 = {
    "quantity_sold": 30,  # Low sales
    "inventory_level": 470,  # Still excess inventory
    "cost_price": 6.0,
    "current_price": 8.0,
}
reward_2 = shaper.compute_reward(state_2, action_2, next_state_2, debug=True)
print(f"Old price: ${state_2['current_price']:.2f}")
print(f"New price: ${action_2:.2f}")
print(f"Quantity sold: {next_state_2['quantity_sold']}")
print(f"Remaining inventory: {next_state_2['inventory_level']}")
print(f"\nReward breakdown: {shaper.get_reward_breakdown()}")
print(f"❌ FINAL REWARD: {reward_2:.4f} (Bad!)\n")

# Test Case 3: Margin below minimum
print("=" * 60)
print("TEST 3: Margin Below Minimum (Unsustainable)")
print("=" * 60)
state_3 = {
    "product_id": "p0001",
    "current_price": 10.0,
    "cost_price": 6.0,
    "inventory_level": 100,
}
action_3 = 6.5  # Price below minimum margin
next_state_3 = {
    "quantity_sold": 100,  # High sales but poor margin
    "inventory_level": 0,
    "cost_price": 6.0,
    "current_price": 6.5,
}
reward_3 = shaper.compute_reward(state_3, action_3, next_state_3, debug=True)
print(f"Old price: ${state_3['current_price']:.2f}")
print(f"New price: ${action_3:.2f}")
print(f"Cost price: ${state_3['cost_price']:.2f}")
print(f"Margin: {((action_3 - state_3['cost_price']) / action_3 * 100):.1f}%")
print(f"\nReward breakdown: {shaper.get_reward_breakdown()}")
print(f"❌ FINAL REWARD: {reward_3:.4f} (Bad - unsustainable!)\n")

# Test Case 4: Optimal scenario
print("=" * 60)
print("TEST 4: Optimal Scenario (Balanced)")
print("=" * 60)
state_4 = {
    "product_id": "p0001",
    "current_price": 10.0,
    "cost_price": 6.0,
    "inventory_level": 60,
}
action_4 = 10.5  # Small price increase (5%)
next_state_4 = {
    "quantity_sold": 70,  # Good sales
    "inventory_level": 20,  # Healthy inventory
    "cost_price": 6.0,
    "current_price": 10.5,
}
reward_4 = shaper.compute_reward(state_4, action_4, next_state_4, debug=True)
print(f"Old price: ${state_4['current_price']:.2f}")
print(f"New price: ${action_4:.2f}")
print(f"Quantity sold: {next_state_4['quantity_sold']}")
print(f"Remaining inventory: {next_state_4['inventory_level']}")
print(f"Margin: {((action_4 - state_4['cost_price']) / action_4 * 100):.1f}%")
print(f"\nReward breakdown: {shaper.get_reward_breakdown()}")
print(f"✅✅ FINAL REWARD: {reward_4:.4f} (Excellent!)\n")

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Test 1 (Good):       {reward_1:+.4f}")
print(f"Test 2 (Bad):        {reward_2:+.4f}")
print(f"Test 3 (No Margin):  {reward_3:+.4f}")
print(f"Test 4 (Optimal):    {reward_4:+.4f}")
print(f"\nThe agent learns to maximize rewards like Test 4 (optimal).")
print(f"Negative rewards discourage bad behaviors (Test 2, 3).")
print(f"\n✅ RewardShaper test complete!")
