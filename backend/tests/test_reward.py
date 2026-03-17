"""Tests for reward function."""
import pytest
from rl.environment.reward_shaper import RewardShaper


def test_reward_computation():
    """Test reward computation."""
    config = {
        "revenue_weight": 1.0,
        "inventory_weight": 0.5,
        "margin_weight": 0.3,
        "stability_weight": 0.2,
    }
    shaper = RewardShaper(config)
    
    state = {"inventory": 100, "price": 10.0, "cost": 5.0}
    action = 12.0
    next_state = {"inventory": 95, "revenue": 120.0, "margin": 7.0}
    
    reward = shaper.compute_reward(state, action, next_state)
    assert isinstance(reward, float)
