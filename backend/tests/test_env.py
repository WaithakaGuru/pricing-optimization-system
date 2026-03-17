"""Tests for price optimization environment."""
import pytest
import numpy as np
from rl.environment.price_env import PriceOptimizationEnv


def test_env_initialization():
    """Test environment initialization."""
    config = {"state_dim": 10, "action_dim": 1, "price_min": 0.1, "price_max": 1000}
    env = PriceOptimizationEnv(config)
    
    assert env.action_space is not None
    assert env.observation_space is not None


def test_env_reset():
    """Test environment reset."""
    config = {"state_dim": 10, "action_dim": 1, "price_min": 0.1, "price_max": 1000}
    env = PriceOptimizationEnv(config)
    
    state, info = env.reset()
    assert state.shape == (10,)


def test_env_step():
    """Test environment step."""
    config = {"state_dim": 10, "action_dim": 1, "price_min": 0.1, "price_max": 1000}
    env = PriceOptimizationEnv(config)
    
    env.reset()
    action = env.action_space.sample()
    state, reward, done, truncated, info = env.step(action)
    
    assert state.shape == (10,)
    assert isinstance(reward, float)
    assert isinstance(done, bool)
