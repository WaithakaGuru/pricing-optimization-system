# 🎯 Complete Model Improvement & Training Plan

## Overview

This document consolidates **all fixes**, **improvements**, and **best practices** for training and deploying your RL pricing models.

---

## Phase 1: Fix Critical Issues ⚠️

### 1. Fix POS Terminal Transaction Bug ✅ DONE

**Location:** `backend/api/routes/pos.py`

- ✅ Consolidated duplicate products into single transaction records
- ✅ Each unique product gets one transaction ID
- ✅ Quantities are summed for duplicate products
- **Test:** Add 2 cabbages + 1 tomato → Should create 2 transaction records

### 2. Fix Reward Shaper ⚠️ HIGH PRIORITY

**Location:** `backend/services/reward_shaper.py`

- **Issues:**
  - PPO getting -9 reward every episode (training broken)
  - SAC reward saturated at 99.8% (not learning)
- **Fixes to apply:**

  ```python
  # Check for sign errors in reward calculation
  revenue = quantity * price  # Should be positive
  cost = quantity * cost_price  # Should be positive

  # Revenue bonus should be positive for good sales
  revenue_bonus = (revenue - baseline) * 0.1
  # NOT: revenue_bonus = -(revenue - baseline) * 0.1

  # Remove aggressive clipping
  # tf: reward = tf.clip_by_value(reward, -100, 100)
  # ✅ Let raw values through, clip only outputs
  ```

- **Steps:**
  1. Add logging to see actual reward values
  2. Fix sign errors
  3. Adjust penalty weights
  4. Test with dummy prices

### 3. Add Comprehensive Logging

**Location:** `backend/services/reward_shaper.py`, `backend/rl/trainer.py`

```python
logger.info(f"Revenue: {revenue}, Cost: {cost}, Margin: {margin:.2%}, Penalty: {penalties}")
logger.info(f"Final reward: {reward:.3f}")
logger.info(f"Episode {episode}: Avg reward {avg_reward:.3f}, Loss {loss:.4f}")
```

---

## Phase 2: Data & Feature Improvements 📊

### 4. Expand Synthetic Training Data

**Current:** 90 days × 10 products
**Target:** 365 days × 20+ products

**Steps:**

1. Edit `backend/utils/synthetic_data.py`
2. Change date range: `timedelta(days=90)` → `timedelta(days=365)`
3. Increase products: `range(10)` → `range(20)` or more
4. Add seasonal patterns for different product categories

```python
# Example: seasonal products
if product_id.startswith("SEASONAL"):
    # Higher demand in certain months
    demand *= (1 + 0.5 * sin(month))
```

### 5. Enhance State Features

**Current:** 12 features
**Add:**

- Time of day (hour as cyclical)
- Day of week (cyclical encoding)
- Competitor prices
- Price momentum (delta from yesterday)
- Stock-out risk indicator
- Demand volatility

```python
state = [
    current_price,
    cost_price,
    margin,
    inventory_level,
    demand_velocity,
    trend,
    seasonality,
    weather_temp,          # Current
    competitor_price,      # New
    price_momentum,        # New - (price_t - price_t-1)
    time_of_day,          # New (0-24)
    day_of_week,          # New (0-6)
]
```

---

## Phase 3: Model Architecture Improvements 🧠

### 6. Expand Network Capacity

**Current:** 128→128 (3.6K params PPO, 5.4K SAC)
**Target:** 256→256→128 (larger networks)

**In `backend/rl/networks/`:**

```python
class PolicyNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 256),  # 128 → 256
            nn.ReLU(),
            nn.Linear(256, 256),        # Add extra layer
            nn.ReLU(),
            nn.Linear(256, 128),        # Hidden middle layer
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )
```

### 7. Improve Hyperparameters

**Update in training scripts:**

```python
# PPO
PPO_CONFIG = {
    "learning_rate": 3e-4,
    "value_lr": 1e-3,           # New - separate LR for value
    "clip_ratio": 0.2,
    "entropy_coeff": 0.01,
    "n_epochs": 5,              # More updates per rollout
    "batch_size": 64,           # Smaller batches
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "normalize_advantages": True,  # New
    "normalize_returns": True      # New
}

# SAC
SAC_CONFIG = {
    "actor_lr": 3e-4,
    "critic_lr": 3e-3,          # Faster critic learning
    "alpha_lr": 1e-4,           # Entropy coefficient tuning
    "entropy_target": -0.5,     # Was -1 (too aggressive)
    "tau": 0.01,                # Faster target updates
    "buffer_size": 500_000,     # Larger replay buffer
}
```

---

## Phase 4: Training Pipeline 🚀

### 8. Use Unified Training Orchestrator

**New script:** `backend/train_all_models.py` ✅ CREATED

```bash
# Train all three models with checkpoint management
python train_all_models.py --agents ppo sac bandit --episodes 500 --cleanup

# Saves checkpoints like:
# ppo_20260326161556_reward45.320.pt
# sac_20260326165010_reward32.100.pt
# bandit_20260326170000_reward78.900.pt

# Automatically deletes weaker checkpoints (keeps top 3)
```

### 9. Implement Checkpoint Management

**New module:** `backend/utils/checkpoint_manager.py` ✅ ENHANCED

Key functions:

```python
find_best_checkpoint(agent_type)        # Get best PPO/SAC/Bandit
list_checkpoints()                      # List all with rewards
cleanup_all_weaker_checkpoints(keep_top_n=3)  # Auto cleanup
print_checkpoint_summary()              # Nice formatted output
```

### 10. Create Checkpoint Status Tool

**New script:** `backend/checkpoints_status.py` ✅ CREATED

```bash
# View all checkpoints
python checkpoints_status.py

# Compare best models
python checkpoints_status.py --compare

# Cleanup weaker ones
python checkpoints_status.py --cleanup --keep-top 3
```

---

## Phase 5: Evaluation & Comparison 📈

### 11. Implement Proper Train/Val/Test Split

**Create:** `backend/split_data.py`

```python
# Training data: 60% (Jan-Jul)
# Validation:   20% (Aug-Sep)
# Test:         20% (Oct-Dec)

train_mask = data.date < "2026-08-01"
val_mask = (data.date >= "2026-08-01") & (data.date < "2026-10-01")
test_mask = data.date >= "2026-10-01"
```

### 12. Track Comprehensive Metrics

**During training:**

- Episode reward
- Average loss (policy + value)
- Entropy (exploration level)
- Value function accuracy

**During evaluation:**

- Revenue uplift vs baseline
- Profit margin maintained
- Inventory turns
- Price deviation per category
- Demand elasticity captured

```python
metrics = {
    "episode": episode,
    "reward": episode_reward,
    "policy_loss": policy_loss,
    "value_loss": value_loss,
    "entropy": entropy,
    "avg_action": action_mean
}
```

### 13. Model Comparison Framework

```bash
# Evaluate all three models on test set
python eval_agent.py --agent_type ppo
python eval_agent.py --agent_type sac
python eval_agent.py --agent_type bandit

# Compare results
python compare_agents.py

# Output:
# PPO:    45.32 reward | $12,340 revenue | 8.3% margin
# SAC:    32.10 reward | $10,120 revenue | 7.2% margin
# Bandit: 78.90 reward | $15,200 revenue | 9.1% margin  ← Best!
```

---

## Phase 6: Production Deployment 🚢

### 14. Update API to Use Best Checkpoint

**In `backend/api/routes/prices.py`:**

```python
from utils.checkpoint_manager import find_best_checkpoint

@router.get("/recommend/{product_id}")
async def recommend_price(product_id: str, agent_type: str = "ppo"):
    """Get price recommendation from best trained model."""

    # Automatically find best checkpoint
    best_ckpt = find_best_checkpoint(agent_type)

    if not best_ckpt:
        raise HTTPException(status_code=500, detail=f"No trained checkpoint")

    agent = load_agent(agent_type, best_ckpt)
    price = agent.recommend_price(product_id)

    return {
        "product_id": product_id,
        "recommended_price": price,
        "agent_type": agent_type,
        "checkpoint": Path(best_ckpt).name
    }
```

### 15. Test in POS Terminal

```bash
# Start API server
python main.py

# Test PPO recommendation
curl "http://localhost:8000/api/prices/recommend/PROD-001?agent_type=ppo"

# Test SAC
curl "http://localhost:8000/api/prices/recommend/PROD-001?agent_type=sac"

# Test Bandit
curl "http://localhost:8000/api/prices/recommend/PROD-001?agent_type=bandit"

# Then test in POS frontend with different agents
```

---

## Implementation Timeline

### Week 1: Critical Fixes

- [ ] Day 1: Fix reward shaper (logging + sign errors)
- [ ] Day 2: Verify reward values are reasonable
- [ ] Day 3: Fix hyperparameters in training scripts
- [ ] Day 4: Run initial training (test run with 100 episodes)

### Week 2: Data & Architecture

- [ ] Day 1: Expand synthetic data (365 days)
- [ ] Day 2: Add new state features
- [ ] Day 3: Increase network capacity
- [ ] Day 4: Implement train/val/test split

### Week 3: Training Pipeline

- [ ] Day 1: Run full training (500 episodes per agent)
- [ ] Day 2: Evaluate all three models
- [ ] Day 3: Compare performance
- [ ] Day 4: Update API to use best checkpoint

### Week 4: Deployment & Refinement

- [ ] Day 1: Test in POS terminal
- [ ] Day 2: Gather feedback, identify issues
- [ ] Day 3: Fine-tune best performing model
- [ ] Day 4: Deploy to production

---

## Quick Start Commands

```bash
# 1. Fix reward shaper
# Edit: backend/services/reward_shaper.py
# - Add debug logging
# - Fix sign errors
# - Adjust penalty weights

# 2. Expand training data
python backend/utils/synthetic_data.py  # Verify 365 days

# 3. Train all models
cd backend/
python train_all_models.py --agents ppo sac bandit --episodes 500 --cleanup

# 4. Check results
python checkpoints_status.py --compare

# 5. Evaluate best models
python eval_agent.py --agent_type ppo
python eval_agent.py --agent_type sac
python eval_agent.py --agent_type bandit

# 6. Update API (see Phase 6 above)

# 7. Test in POS
# Start API server and test recommendations
```

---

## Success Criteria

✅ **Phase 1 (Fixes):**

- PPO reward > 0 (not always -9)
- SAC reward varies (not stuck at 99.8%)
- Training loss decreases over episodes

✅ **Phase 2 (Data):**

- 365 days of synthetic data
- 20+ products
- Multiple state features (>15)

✅ **Phase 3 (Architecture):**

- Network size: 256→256→128
- Total params: 10K+ (was 5K)

✅ **Phase 4 (Training):**

- All three models train successfully
- Checkpoints auto-save on improvements
- Weaker checkpoints auto-deleted

✅ **Phase 5 (Evaluation):**

- All models can be evaluated
- Clear winner identified
- Metrics tracked over time

✅ **Phase 6 (Deployment):**

- API uses `find_best_checkpoint()`
- POS terminal shows recommendations
- Recommendations improve revenue

---

## Key Files

| File                                  | Purpose                           |
| ------------------------------------- | --------------------------------- |
| `backend/train_all_models.py`         | Unified trainer for all 3 agents  |
| `backend/checkpoints_status.py`       | View & manage checkpoints         |
| `backend/utils/checkpoint_manager.py` | Checkpoint API functions          |
| `backend/services/reward_shaper.py`   | [FIX REQUIRED] Reward calculation |
| `backend/rl/trainer.py`               | Training loop (needs fixes)       |
| `MODEL_TRAINING_GUIDE.md`             | Detailed training manual          |
| `CHECKPOINT_QUICK_REFERENCE.md`       | Quick commands reference          |
| `MODEL_TRAINING_ANALYSIS.md`          | Architecture analysis             |

---

## Next Steps

1. **Today:** Fix reward shaper and test with logging
2. **Tomorrow:** Expand synthetic data to 365 days
3. **Day 3-4:** Run full training and evaluate
4. **Day 5+:** Deploy and iterate

---

**You've got this! 🚀 The checkpoint system will make your life much easier.**
