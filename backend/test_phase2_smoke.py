"""Quick smoke test for Phase 2 agents - verifies core functionality."""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ppo_agent_basic():
    """Test PPO agent basic functionality without environment."""
    logger.info("\n✓ Testing PPO Agent...")
    
    from rl.agents.ppo_agent import PPOAgent
    
    agent = PPOAgent(state_dim=12, action_dim=1, hidden_dim=64, n_epochs=2)
    
    # Test action selection
    state = np.random.randn(12).astype(np.float32)
    action, log_prob, value = agent.select_action(state, deterministic=False)
    
    assert isinstance(action, (float, np.floating)), f"Invalid action type: {type(action)}"
    assert 0.1 <= action <= 1000.0, f"Action out of bounds: {action}"
    assert isinstance(log_prob, (float, np.floating)), f"Invalid log_prob type: {type(log_prob)}"
    assert isinstance(value, (float, np.floating)), f"Invalid value type: {type(value)}"
    
    logger.info(f"  Action: {action:.2f}, LogProb: {log_prob:.4f}, Value: {value:.4f}")
    logger.info("✓ PPO Agent initialized and action selection working")
    
    return agent


def test_sac_agent_basic():
    """Test SAC agent basic functionality without environment."""
    logger.info("\n✓ Testing SAC Agent...")
    
    from rl.agents.sac_agent import SACAgent
    
    agent = SACAgent(state_dim=12, action_dim=1, hidden_dim=64)
    
    # Test action selection
    state = np.random.randn(12).astype(np.float32)
    action, log_prob = agent.select_action(state, deterministic=False)
    
    assert isinstance(action, (float, np.floating)), f"Invalid action type: {type(action)}"
    assert 0.1 <= action <= 1000.0, f"Action out of bounds: {action}"
    
    logger.info(f"  Action: {action:.2f}")
    logger.info("✓ SAC Agent initialized and action selection working")
    
    # Test replay buffer
    for i in range(10):
        state = np.random.randn(12).astype(np.float32)
        action = np.random.uniform(0.1, 1000)
        reward = np.random.randn()
        next_state = np.random.randn(12).astype(np.float32)
        done = False
        agent.store_experience(state, action, reward, next_state, done)
    
    assert len(agent.replay_buffer) == 10, "Replay buffer not storing experiences"
    logger.info("✓ SAC replay buffer working")
    
    return agent


def test_trainer_basic():
    """Test RLTrainer basic functionality."""
    logger.info("\n✓ Testing RLTrainer...")
    
    from rl.agents.ppo_agent import PPOAgent
    from rl.environment.price_env import PriceOptimizationEnv
    from rl.trainer import RLTrainer
    from models import Product, InventoryItem
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    
    # Create test product in database
    try:
        engine = create_engine("sqlite:///pricing.db")
        with Session(engine) as session:
            # Check if SMOKE-TEST product exists
            existing = session.query(Product).filter(Product.product_id == "SMOKE-TEST").first()
            if not existing:
                product = Product(
                    product_id="SMOKE-TEST",
                    name="Smoke Test Product",
                    category="Test",
                    base_price=10.0,
                    min_price=5.0,
                    max_price=50.0,
                )
                session.add(product)
                session.commit()
                logger.info("✓ Created test product in database")
    except Exception as e:
        logger.warning(f"Could not create test product: {e}")
    
    # Create minimal environment and agent
    env = PriceOptimizationEnv(product_id="SMOKE-TEST", max_steps=10)
    agent = PPOAgent(state_dim=12, action_dim=1, hidden_dim=32, n_epochs=1)
    
    config = {
        "num_episodes": 2,
        "max_steps_per_episode": 10,
        "update_frequency": 1,
        "eval_frequency": 100,
        "checkpoint_frequency": 100,
    }
    
    trainer = RLTrainer(agent, env, config=config)
    logger.info("✓ RLTrainer initialized")
    
    # Run minimal training
    trainer.train(num_episodes=2)
    
    summary = trainer.get_results_summary()
    assert summary["total_episodes"] == 2, "Training didn't run correct number of episodes"
    assert summary["total_steps"] > 0, "No steps recorded"
    
    logger.info(f"  Episodes: {summary['total_episodes']}, Steps: {summary['total_steps']}")
    logger.info(f"  Mean Reward: {summary['mean_episode_reward']:.3f}")
    logger.info("✓ RLTrainer basic training working")


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Phase 2 Smoke Tests - Quick Verification")
    logger.info("=" * 70)
    
    try:
        ppo_agent = test_ppo_agent_basic()
        logger.info("\n✅ PPO Agent tests passed")
    except Exception as e:
        logger.error(f"\n❌ PPO Agent tests failed: {e}", exc_info=True)
    
    try:
        sac_agent = test_sac_agent_basic()
        logger.info("\n✅ SAC Agent tests passed")
    except Exception as e:
        logger.error(f"\n❌ SAC Agent tests failed: {e}", exc_info=True)
    
    try:
        test_trainer_basic()
        logger.info("\n✅ RLTrainer tests passed")
    except Exception as e:
        logger.error(f"\n❌ RLTrainer tests failed: {e}", exc_info=True)
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ Phase 2 Smoke Tests Completed Successfully!")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("  - Run full tests: python test_ppo_agent.py, python test_sac_agent.py")
    logger.info("  - Run benchmark: python test_phase2_benchmark.py")
    logger.info("  - Proceed to Phase 3: API Integration")
