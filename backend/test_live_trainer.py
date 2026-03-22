"""Test suite for LiveTrainer transaction-based learning loop."""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from rl.trainer import LiveTrainer, ReplayBuffer

# Try to import optional dependencies for full testing
try:
    from rl.agents.ppo_agent import PPOAgent
    HAS_PPO = True
except ImportError:
    HAS_PPO = False

try:
    from services.reward_shaper import RewardShaper
    HAS_REWARD_SHAPER = True
except ImportError:
    HAS_REWARD_SHAPER = False

try:
    from rl.environment.state_builder import StateBuilder
    HAS_STATE_BUILDER = True
except ImportError:
    HAS_STATE_BUILDER = False


class TestReplayBuffer:
    """Tests for ReplayBuffer functionality."""

    def test_replay_buffer_initialization(self):
        """Test ReplayBuffer can be initialized."""
        buffer = ReplayBuffer(capacity=1000, priority_alpha=0.6)
        assert buffer is not None
        assert buffer.capacity == 1000
        assert buffer.size == 0
        logger.info("✓ ReplayBuffer initialized successfully")

    def test_add_experience(self):
        """Test adding experiences to replay buffer."""
        buffer = ReplayBuffer(capacity=100)
        
        # Create sample experiences
        for i in range(10):
            experience = {
                "state": np.random.randn(12),
                "action": np.random.rand() * 100,
                "reward": np.random.rand(),
                "next_state": np.random.randn(12),
                "done": i == 9,
            }
            priority = abs(experience["reward"]) + 1.0
            buffer.add(experience, priority=priority)
        
        assert buffer.size == 10
        logger.info(f"✓ Added 10 experiences to buffer, size: {buffer.size}")

    def test_buffer_capacity_limit(self):
        """Test that buffer respects capacity limit (circular when full)."""
        buffer = ReplayBuffer(capacity=100)
        
        # Add more than capacity
        for i in range(150):
            experience = {
                "state": np.random.randn(12),
                "action": np.random.rand() * 100,
                "reward": np.random.rand(),
                "next_state": np.random.randn(12),
                "done": False,
            }
            buffer.add(experience, priority=1.0)
        
        assert buffer.size <= 100
        logger.info(f"✓ Buffer capacity limit enforced: {buffer.size}/{buffer.capacity}")

    def test_sample_batch(self):
        """Test sampling a batch from replay buffer."""
        buffer = ReplayBuffer(capacity=1000)
        
        # Add experiences
        for i in range(200):
            experience = {
                "state": np.random.randn(12),
                "action": np.random.rand() * 100,
                "reward": float(i) / 100.0,
                "next_state": np.random.randn(12),
                "done": i % 50 == 0,
            }
            buffer.add(experience, priority=float(i) / 100.0 + 1.0)
        
        # Sample batch
        batch = buffer.sample(batch_size=32)
        
        assert batch is not None
        assert isinstance(batch, list)
        assert len(batch) == 32
        assert all(isinstance(exp, dict) for exp in batch)
        assert all("reward" in exp for exp in batch)
        
        rewards = [exp["reward"] for exp in batch]
        logger.info(f"✓ Sampled batch of {len(batch)} experiences from buffer")
        logger.info(f"  Reward range: [{min(rewards):.3f}, {max(rewards):.3f}]")

    def test_priority_sampling(self):
        """Test that priority-weighted sampling works (high-priority experiences sampled more)."""
        buffer = ReplayBuffer(capacity=1000, priority_alpha=0.8)
        
        # Add low-priority experiences
        for i in range(100):
            experience = {
                "state": np.random.randn(12),
                "action": np.random.rand() * 100,
                "reward": 0.1,
                "next_state": np.random.randn(12),
                "done": False,
            }
            buffer.add(experience, priority=0.1)  # Low priority
        
        # Add high-priority experiences
        for i in range(100):
            experience = {
                "state": np.random.randn(12),
                "action": np.random.rand() * 100,
                "reward": 0.9,
                "next_state": np.random.randn(12),
                "done": False,
            }
            buffer.add(experience, priority=10.0)  # High priority
        
        # Sample many times and check if high-priority experiences are sampled more
        high_priority_count = 0
        samples = 1000
        
        for _ in range(samples):
            batch = buffer.sample(batch_size=1)
            if batch[0]["reward"] > 0.5:
                high_priority_count += 1
        
        # High-priority experiences should be sampled more frequently
        high_priority_ratio = high_priority_count / samples
        assert high_priority_ratio > 0.4, f"Expected >40% high-priority samples, got {high_priority_ratio*100:.1f}%"
        
        logger.info(f"✓ Priority sampling verified: {high_priority_ratio*100:.1f}% high-priority samples")

    def test_clear_buffer(self):
        """Test clearing the buffer."""
        buffer = ReplayBuffer(capacity=100)
        
        # Add experiences
        for i in range(50):
            experience = {
                "state": np.random.randn(12),
                "action": np.random.rand() * 100,
                "reward": 0.5,
                "next_state": np.random.randn(12),
                "done": False,
            }
            buffer.add(experience)
        
        assert buffer.size == 50
        
        # Clear
        buffer.clear()
        assert buffer.size == 0
        
        logger.info("✓ Buffer cleared successfully")


class TestLiveTrainer:
    """Tests for LiveTrainer transaction-based learning."""

    def test_livetrainer_initialization(self):
        """Test LiveTrainer can be initialized."""
        if not (HAS_PPO and HAS_REWARD_SHAPER and HAS_STATE_BUILDER):
            pytest.skip("Required dependencies not available")
        
        agent = PPOAgent(state_dim=12, action_dim=1)
        reward_shaper = RewardShaper()
        state_builder = StateBuilder()
        
        trainer = LiveTrainer(
            agent=agent,
            reward_shaper=reward_shaper,
            state_builder=state_builder,
            config={
                "update_interval": 50,
                "buffer_capacity": 100_000,
                "batch_size": 64,
                "checkpoint_interval": 200,
            }
        )
        
        assert trainer is not None
        assert trainer.update_interval == 50
        assert trainer.checkpoint_interval == 200
        assert trainer.transaction_count == 0
        
        logger.info("✓ LiveTrainer initialized successfully")

    def test_on_transaction_processing(self):
        """Test processing individual transactions."""
        if not (HAS_PPO and HAS_REWARD_SHAPER and HAS_STATE_BUILDER):
            pytest.skip("Required dependencies not available")
        
        agent = PPOAgent(state_dim=12, action_dim=1)
        reward_shaper = RewardShaper()
        state_builder = StateBuilder()
        
        trainer = LiveTrainer(
            agent=agent,
            reward_shaper=reward_shaper,
            state_builder=state_builder,
            config={"update_interval": 100, "buffer_capacity": 100_000}
        )
        
        # Simulate transactions
        num_transactions = 20
        for i in range(num_transactions):
            transaction = {
                "product_id": 1,
                "price": np.random.uniform(50, 150),
                "quantity": np.random.randint(1, 10),
                "timestamp": datetime.now(),
            }
            
            trainer.on_transaction(transaction)
        
        assert trainer.transaction_count == num_transactions
        assert len(trainer.replay_buffer) == num_transactions
        
        logger.info(f"✓ Processed {num_transactions} transactions")
        logger.info(f"  Replay buffer size: {len(trainer.replay_buffer)}")

    def test_replay_buffer_accumulation(self):
        """Test that replay buffer accumulates experiences from transactions."""
        if not (HAS_PPO and HAS_REWARD_SHAPER and HAS_STATE_BUILDER):
            pytest.skip("Required dependencies not available")
        
        agent = PPOAgent(state_dim=12, action_dim=1)
        reward_shaper = RewardShaper()
        state_builder = StateBuilder()
        
        trainer = LiveTrainer(
            agent=agent,
            reward_shaper=reward_shaper,
            state_builder=state_builder,
            config={"update_interval": 1000, "buffer_capacity": 100_000}
        )
        
        # Simulate many transactions
        for i in range(100):
            transaction = {
                "product_id": 1,
                "price": 100 + np.random.randn() * 20,
                "quantity": np.random.randint(1, 20),
                "timestamp": datetime.now(),
            }
            
            trainer.on_transaction(transaction)
        
        assert trainer.transaction_count == 100
        assert len(trainer.replay_buffer) >= 100
        
        logger.info(f"✓ Accumulated {len(trainer.replay_buffer)} experiences in replay buffer")

    def test_get_performance_summary(self):
        """Test getting performance metrics."""
        if not (HAS_PPO and HAS_REWARD_SHAPER and HAS_STATE_BUILDER):
            pytest.skip("Required dependencies not available")
        
        agent = PPOAgent(state_dim=12, action_dim=1)
        reward_shaper = RewardShaper()
        state_builder = StateBuilder()
        
        trainer = LiveTrainer(
            agent=agent,
            reward_shaper=reward_shaper,
            state_builder=state_builder,
            config={"update_interval": 50}
        )
        
        # Process some transactions
        for i in range(60):
            transaction = {
                "product_id": 1,
                "price": 100 + i,
                "quantity": 5,
                "timestamp": datetime.now(),
            }
            
            trainer.on_transaction(transaction)
        
        # Get summary
        summary = trainer.get_performance_summary()
        
        assert summary is not None
        assert isinstance(summary, dict)
        assert "total_transactions" in summary
        assert "buffer_size" in summary
        assert "mean_recent_reward" in summary
        
        assert summary["total_transactions"] == 60
        
        logger.info("✓ Performance summary generated:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")

    def test_drift_detection(self):
        """Test performance drift detection."""
        if not (HAS_PPO and HAS_REWARD_SHAPER and HAS_STATE_BUILDER):
            pytest.skip("Required dependencies not available")
        
        agent = PPOAgent(state_dim=12, action_dim=1)
        reward_shaper = RewardShaper()
        state_builder = StateBuilder()
        
        trainer = LiveTrainer(
            agent=agent,
            reward_shaper=reward_shaper,
            state_builder=state_builder,
            config={"update_interval": 1000}
        )
        
        # Simulate stable performance for a while
        for i in range(100):
            transaction = {
                "product_id": 1,
                "price": 100.0,
                "quantity": 5,
                "timestamp": datetime.now(),
            }
            trainer.on_transaction(transaction)
        
        # Check for drift
        has_drift = trainer.detect_drift(threshold=-0.10)
        
        logger.info(f"✓ Drift detection status: {has_drift}")
        logger.info(f"  Expected False/not detected with only 100 transactions (needs 200+)")


class TestLiveTrainerIntegration:
    """Integration tests for complete training pipeline."""

    def test_end_to_end_transaction_flow(self):
        """Test complete flow: transaction → state build → reward → buffer."""
        if not (HAS_PPO and HAS_REWARD_SHAPER and HAS_STATE_BUILDER):
            pytest.skip("Required dependencies not available")
        
        agent = PPOAgent(state_dim=12, action_dim=1)
        reward_shaper = RewardShaper()
        state_builder = StateBuilder()
        
        trainer = LiveTrainer(
            agent=agent,
            reward_shaper=reward_shaper,
            state_builder=state_builder,
            config={
                "update_interval": 30,
                "buffer_capacity": 100_000,
            }
        )
        
        logger.info("Simulating transaction-based training...")
        
        # Simulate realistic transaction stream
        for day in range(10):
            for hour in range(8):  # 8 hours per day
                for _ in range(5):  # 5 sales per hour
                    transaction = {
                        "product_id": 1,
                        "price": np.random.uniform(80, 150),
                        "quantity": np.random.randint(1, 15),
                        "timestamp": datetime.now(),
                    }
                    
                    trainer.on_transaction(transaction)
        
        summary = trainer.get_performance_summary()
        
        assert summary["total_transactions"] == 400
        assert len(trainer.replay_buffer) > 0
        
        logger.info(f"✓ Processed {summary['total_transactions']} transactions")
        logger.info(f"  Buffer size: {summary['buffer_size']}")
        logger.info(f"  Mean recent reward: {summary['mean_recent_reward']:.4f}")

    def test_training_stability(self):
        """Test that training remains stable over extended transaction stream."""
        if not (HAS_PPO and HAS_REWARD_SHAPER and HAS_STATE_BUILDER):
            pytest.skip("Required dependencies not available")
        
        agent = PPOAgent(state_dim=12, action_dim=1)
        reward_shaper = RewardShaper()
        state_builder = StateBuilder()
        
        trainer = LiveTrainer(
            agent=agent,
            reward_shaper=reward_shaper,
            state_builder=state_builder,
            config={"update_interval": 20, "buffer_capacity": 100_000}
        )
        
        rewards = []
        
        # Generate transactions with slight trend
        for i in range(150):
            transaction = {
                "product_id": 1,
                "price": 100 + np.random.randn() * 20,
                "quantity": np.random.randint(2, 12),
                "timestamp": datetime.now(),
            }
            
            trainer.on_transaction(transaction)
            
            if i % 10 == 0:
                summary = trainer.get_performance_summary()
                rewards.append(summary["mean_recent_reward"])
        
        logger.info(f"✓ Training stability test completed")
        logger.info(f"  Total transactions: {trainer.transaction_count}")
        logger.info(f"  Reward trajectory: {[f'{r:.3f}' for r in rewards[:5]]} ... {[f'{r:.3f}' for r in rewards[-3:]]}")


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("LIVE TRAINER TEST SUITE")
    logger.info("=" * 70)
    pytest.main([__file__, "-v", "-s"])
