"""Test PPO Agent."""
import numpy as np
import torch
import logging
from rl.agents.ppo_agent import PPOAgent
from rl.environment.price_env import PriceOptimizationEnv
from rl.trainer import RLTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ppo_action_selection():
    """Test that PPO can select actions."""
    logger.info("Testing PPO action selection...")
    
    agent = PPOAgent(state_dim=12, action_dim=1)
    state = np.random.randn(12).astype(np.float32)
    
    # Non-deterministic action
    action, log_prob, value = agent.select_action(state, deterministic=False)
    
    assert isinstance(action, (float, np.floating)), f"Action should be float, got {type(action)}"
    assert 0.1 <= action <= 1000.0, f"Action {action} out of bounds"
    assert isinstance(log_prob, (float, np.floating)), "Log prob should be float"
    assert isinstance(value, (float, np.floating)), "Value should be float"
    
    # Deterministic action
    action_det, _, _ = agent.select_action(state, deterministic=True)
    assert isinstance(action_det, (float, np.floating)), "Deterministic action should be float"
    
    logger.info("✓ PPO action selection passed")


def test_ppo_experience_storage():
    """Test that PPO can store and clear experience."""
    logger.info("Testing PPO experience storage...")
    
    agent = PPOAgent()
    
    # Store multiple experiences
    for i in range(10):
        state = np.random.randn(12)
        action = np.random.uniform(0.1, 1000)
        reward = np.random.randn()
        log_prob = np.random.randn()
        value = np.random.randn()
        done = i % 2 == 0
        
        agent.store_experience(state, action, reward, log_prob, value, done)
    
    assert len(agent.states) == 10, "Should have stored 10 experiences"
    
    # Clear buffer
    agent.clear_buffer()
    assert len(agent.states) == 0, "Buffer should be empty after clear"
    
    logger.info("✓ PPO experience storage passed")


def test_ppo_update():
    """Test that PPO can perform updates."""
    logger.info("Testing PPO update...")
    
    agent = PPOAgent(hidden_dim=64)
    
    # Generate some experience
    for _ in range(20):
        state = np.random.randn(12).astype(np.float32)
        action = np.random.uniform(0.1, 1000)
        reward = np.random.randn()
        log_prob = np.random.randn()
        value = np.random.randn()
        done = False
        
        agent.store_experience(state, action, reward, log_prob, value, done)
    
    # Try update (should complete without error)
    agent.update()
    
    assert len(agent.states) == 0, "Buffer should be cleared after update"
    
    logger.info("✓ PPO update passed")


def test_ppo_with_env():
    """Test PPO agent training with environment."""
    logger.info("Testing PPO with environment...")
    
    env = PriceOptimizationEnv(product_id="PROD-TEST")
    agent = PPOAgent(state_dim=12, action_dim=1, hidden_dim=64, n_epochs=2)
    
    # Run a few steps
    state, info = env.reset()
    total_reward = 0
    
    for step in range(20):
        action, log_prob, value = agent.select_action(state)
        next_state, reward, terminated, truncated, info = env.step(action)
        
        agent.store_experience(state, action, reward, log_prob, value, terminated or truncated)
        
        total_reward += reward
        state = next_state
        
        if terminated or truncated:
            break
    
    # Update agent
    agent.update()
    
    logger.info(f"✓ PPO with environment passed (total reward: {total_reward:.3f})")


def test_ppo_checkpointing():
    """Test PPO checkpoint save/load."""
    logger.info("Testing PPO checkpointing...")
    
    import tempfile
    import os
    
    agent = PPOAgent()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = os.path.join(tmpdir, "ppo_test.pt")
        
        # Save checkpoint
        agent.save_checkpoint(checkpoint_path)
        assert os.path.exists(checkpoint_path), "Checkpoint file not created"
        
        # Load checkpoint
        agent2 = PPOAgent()
        agent2.load_checkpoint(checkpoint_path)
        
        logger.info("✓ PPO checkpointing passed")


def test_ppo_with_trainer():
    """Test PPO training loop with RLTrainer."""
    logger.info("Testing PPO with RLTrainer...")
    
    env = PriceOptimizationEnv(product_id="PROD-TRAIN", max_steps=50)
    agent = PPOAgent(state_dim=12, action_dim=1, hidden_dim=64, n_epochs=2)
    
    config = {
        "num_episodes": 5,
        "max_steps_per_episode": 50,
        "update_frequency": 1,
        "eval_frequency": 2,
        "checkpoint_frequency": 100,
    }
    
    trainer = RLTrainer(agent, env, config=config)
    
    # Train for a few episodes
    trainer.train(num_episodes=5)
    
    # Check results
    summary = trainer.get_results_summary()
    assert summary["total_episodes"] == 5
    assert summary["total_steps"] > 0
    
    logger.info(f"✓ PPO with trainer passed: {summary}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Running PPO Agent Tests")
    logger.info("=" * 60)
    
    test_ppo_action_selection()
    test_ppo_experience_storage()
    test_ppo_update()
    test_ppo_with_env()
    test_ppo_checkpointing()
    test_ppo_with_trainer()
    
    logger.info("=" * 60)
    logger.info("✓ All PPO tests passed!")
    logger.info("=" * 60)
