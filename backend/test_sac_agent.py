"""Test SAC Agent."""
import numpy as np
import torch
import logging
from rl.agents.sac_agent import SACAgent
from rl.environment.price_env import PriceOptimizationEnv
from rl.trainer import RLTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_sac_action_selection():
    """Test that SAC can select actions."""
    logger.info("Testing SAC action selection...")
    
    agent = SACAgent(state_dim=12, action_dim=1)
    state = np.random.randn(12).astype(np.float32)
    
    # Stochastic action (with exploration)
    action, log_prob = agent.select_action(state, deterministic=False)
    
    assert isinstance(action, (float, np.floating)), f"Action should be float, got {type(action)}"
    assert 0.1 <= action <= 1000.0, f"Action {action} out of bounds [0.1, 1000]"
    
    # Deterministic action
    action_det, _ = agent.select_action(state, deterministic=True)
    assert isinstance(action_det, (float, np.floating)), f"Action should be float, got {type(action_det)}"
    assert 0.1 <= action_det <= 1000.0, f"Deterministic action {action_det} out of bounds"
    
    logger.info("✓ SAC action selection passed")


def test_sac_replay_buffer():
    """Test that SAC replay buffer works."""
    logger.info("Testing SAC replay buffer...")
    
    agent = SACAgent(buffer_size=1000)
    
    # Store experiences
    for i in range(100):
        state = np.random.randn(12)
        action = np.random.uniform(0.1, 1000)
        reward = np.random.randn()
        next_state = np.random.randn(12)
        done = i % 10 == 0
        
        agent.store_experience(state, action, reward, next_state, done)
    
    assert len(agent.replay_buffer) == 100, "Should have 100 experiences in buffer"
    
    logger.info("✓ SAC replay buffer passed")


def test_sac_update():
    """Test that SAC can perform updates."""
    logger.info("Testing SAC update...")
    
    agent = SACAgent(hidden_dim=64, batch_size=32)
    
    # Fill replay buffer
    for i in range(50):
        state = np.random.randn(12).astype(np.float32)
        action = np.random.uniform(0.1, 1000)
        reward = np.random.randn()
        next_state = np.random.randn(12).astype(np.float32)
        done = i % 5 == 0
        
        agent.store_experience(state, action, reward, next_state, done)
    
    # Perform update
    agent.update(n_updates=5)
    
    logger.info("✓ SAC update passed")


def test_sac_with_env():
    """Test SAC agent with environment."""
    logger.info("Testing SAC with environment...")
    
    env = PriceOptimizationEnv(product_id="SAC-TEST")
    agent = SACAgent(state_dim=12, action_dim=1, hidden_dim=64)
    
    # Collect experience
    state, info = env.reset()
    total_reward = 0
    
    for step in range(30):
        action, _ = agent.select_action(state)
        next_state, reward, terminated, truncated, info = env.step(action)
        
        agent.store_experience(state, action, reward, next_state, terminated or truncated)
        
        total_reward += reward
        state = next_state
        
        if terminated or truncated:
            break
    
    # Perform updates
    if len(agent.replay_buffer) >= agent.batch_size:
        agent.update(n_updates=5)
    
    logger.info(f"✓ SAC with environment passed (total reward: {total_reward:.3f})")


def test_sac_action_scaling():
    """Test SAC action scaling."""
    logger.info("Testing SAC action scaling...")
    
    agent = SACAgent()
    
    # Test scaling from [-1, 1] to [0.1, 1000]
    action_normal = np.array([0.0])
    action_scaled = agent._scale_action(action_normal)
    expected = 500.05
    assert abs(action_scaled - expected) < 0.1, f"Expected ~{expected}, got {action_scaled}"
    
    # Test unscaling
    action_unscaled = agent._unscale_action(action_scaled)
    assert abs(action_unscaled - action_normal) < 0.01, "Unscaled action doesn't match"
    
    # Test bounds
    action_min = np.array([-1.0])
    action_max = np.array([1.0])
    
    scaled_min = agent._scale_action(action_min)
    scaled_max = agent._scale_action(action_max)
    
    assert 0.0 <= scaled_min <= 1000.0, f"Scaled min {scaled_min} out of bounds"
    assert 0.0 <= scaled_max <= 1000.0, f"Scaled max {scaled_max} out of bounds"
    
    logger.info("✓ SAC action scaling passed")


def test_sac_checkpointing():
    """Test SAC checkpoint save/load."""
    logger.info("Testing SAC checkpointing...")
    
    import tempfile
    import os
    
    agent = SACAgent()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_path = os.path.join(tmpdir, "sac_test.pt")
        
        # Save checkpoint
        agent.save_checkpoint(checkpoint_path)
        assert os.path.exists(checkpoint_path), "Checkpoint file not created"
        
        # Load checkpoint
        agent2 = SACAgent()
        agent2.load_checkpoint(checkpoint_path)
        
        assert agent2.alpha == agent.alpha, "Alpha not loaded correctly"
        
        logger.info("✓ SAC checkpointing passed")


def test_sac_soft_updates():
    """Test SAC target network soft updates."""
    logger.info("Testing SAC soft updates...")
    
    agent = SACAgent(hidden_dim=64)
    
    # Store baseline target params
    baseline_q1_target = [p.clone() for p in agent.q1_target.parameters()]
    
    # Modify online Q1 network
    for param in agent.q1.parameters():
        param.data += 1.0
    
    # Perform soft update
    agent._soft_update_target_networks()
    
    # Check that target was updated (but not fully)
    updated_q1_target = agent.q1_target.parameters()
    
    for i, (baseline, updated) in enumerate(zip(baseline_q1_target, updated_q1_target)):
        diff = (updated - baseline).abs().mean().item()
        assert diff > 0, f"Target network {i} was not updated"
        assert diff < 1.0, f"Target network {i} was updated too much"
    
    logger.info("✓ SAC soft updates passed")


def test_sac_with_trainer():
    """Test SAC training loop with RLTrainer."""
    logger.info("Testing SAC with RLTrainer...")
    
    env = PriceOptimizationEnv(product_id="SAC-TRAIN", max_steps=50)
    agent = SACAgent(state_dim=12, action_dim=1, hidden_dim=64)
    
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
    
    logger.info(f"✓ SAC with trainer passed: {summary}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Running SAC Agent Tests")
    logger.info("=" * 60)
    
    test_sac_action_selection()
    test_sac_replay_buffer()
    test_sac_update()
    test_sac_with_env()
    test_sac_action_scaling()
    test_sac_checkpointing()
    test_sac_soft_updates()
    test_sac_with_trainer()
    
    logger.info("=" * 60)
    logger.info("✓ All SAC tests passed!")
    logger.info("=" * 60)
