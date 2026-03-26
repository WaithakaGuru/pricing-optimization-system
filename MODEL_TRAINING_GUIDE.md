# 🤖 Model Training & Checkpoint Management Guide

## Overview

This guide explains how to:

1. **Train all three models** (PPO, SAC, Contextual Bandit) properly
2. **Identify and manage checkpoints** automatically
3. **Keep only the best performing models** and delete weaker ones
4. **Evaluate and compare** model performance
5. **Deploy the best model** to production

---

## Quick Start: Train All Models

### One-Command Training

```bash
cd backend/
python train_all_models.py --agents ppo sac bandit --episodes 500 --cleanup
```

**What this does:**

- ✅ Trains PPO with 500 episodes
- ✅ Trains SAC with 500 episodes
- ✅ Trains Bandit with ~100 episodes (trains faster)
- ✅ Automatically keeps only top 3 checkpoints per agent
- ✅ Deletes weaker checkpoints to save disk space

### Training Options

```bash
# Train only PPO, keep top 5 checkpoints
python train_all_models.py --agents ppo --episodes 1000 --keep-top 5

# Train SAC and Bandit, no cleanup (keep all)
python train_all_models.py --agents sac bandit --no-cleanup

# Quick training (250 episodes)
python train_all_models.py --agents ppo sac bandit --episodes 250
```

---

## Checkpoint System

### Understanding Checkpoint Filenames

```
ppo_20260326161556_reward45.320.pt
├─ ppo          = Agent type (ppo, sac, bandit)
├─ 20260326161556 = Timestamp (YYYYMMDDhhmmss)
├─ reward45.320  = Reward score achieved in training
└─ .pt          = PyTorch format
```

### How Checkpoints Are Managed

#### 1. **During Training**: Save Improvements

```python
# In train_agent_synthetic_v2.py:
if episode_reward > best_reward:
    checkpoint_path = Path(save_dir) / f"PPO_{timestamp}_reward{episode_reward:.3f}.pt"
    agent.save_checkpoint(str(checkpoint_path))
    # ✅ Only saves when agent improves
```

#### 2. **After Training**: Cleanup Weaker Checkpoints

```python
# Automatic cleanup after training
cleanup_all_weaker_checkpoints(keep_top_n=3)

# Before cleanup:
# ❌ ppo_20260326101010_reward35.200.pt  (old, weak)
# ❌ ppo_20260326121010_reward40.100.pt  (better)
# ✅ ppo_20260326141010_reward45.320.pt  (BEST - kept)
# ✅ ppo_20260326151010_reward44.890.pt  (2nd best - kept)
# ✅ ppo_20260326161010_reward45.100.pt  (3rd best - kept)
```

---

## API: Checkpoint Management Functions

### Find Best Checkpoint

```python
from utils.checkpoint_manager import find_best_checkpoint

# Get the best performing PPO checkpoint
best_ppo = find_best_checkpoint("ppo")
# Returns: "/path/to/ppo_20260326161556_reward45.320.pt"
```

### List All Checkpoints

```python
from utils.checkpoint_manager import list_checkpoints

checkpoints = list_checkpoints()
# Returns:
# {
#   "ppo": [
#     {"filename": "ppo_..._reward45.320.pt", "reward_score": 45.32, ...},
#     {"filename": "ppo_..._reward44.890.pt", "reward_score": 44.89, ...},
#   ],
#   "sac": [...],
#   "bandit": [...]
# }

# Iterate through checkpoints
for agent_type, checkpoints_list in checkpoints.items():
    print(f"\n{agent_type}:")
    for idx, ckpt in enumerate(checkpoints_list, 1):
        print(f"  {idx}. {ckpt['filename']} (reward: {ckpt['reward_score']:.3f})")
```

### Print Checkpoint Summary

```python
from utils.checkpoint_manager import print_checkpoint_summary

print_checkpoint_summary()
# Output:
# 📊 CHECKPOINT SUMMARY:
# ================================================================================
#
# PPO:
# ────────────────────────────────────────────────────────────────────────────────
#   1. ppo_20260326161556_reward45.320.pt          | Reward: 45.320 | Size:   8.45MB | ⭐ BEST
#   2. ppo_20260326151010_reward45.100.pt          | Reward: 45.100 | Size:   8.42MB
#   3. ppo_20260326141010_reward44.890.pt          | Reward: 44.890 | Size:   8.41MB
```

### Cleanup Weaker Checkpoints

```python
from utils.checkpoint_manager import cleanup_all_weaker_checkpoints

# Keep only top 3 checkpoints per agent type
results = cleanup_all_weaker_checkpoints(keep_top_n=3)
# Returns: {"ppo": (2, 3), "sac": (1, 3), "bandit": (0, 2)}
# Format: agent_type: (deleted_count, remaining_count)

# More aggressive: keep only top 1 (best per agent)
results = cleanup_all_weaker_checkpoints(keep_top_n=1)
```

---

## Complete Training Workflow

### Step 1: Prepare Data & Environment

```bash
cd backend/

# Make sure all dependencies are installed
pip install -r requirements.txt

# Check database is initialized
python init_db.py  # Creates pricing.db if missing
```

### Step 2: Train All Three Models

```bash
# This will take 10-20 minutes depending on episodes
python train_all_models.py --agents ppo sac bandit --episodes 500 --cleanup
```

**What's happening:**

- 📊 Synthetic data is loaded (90 days × 10 products)
- 🧠 PPO agent trains for 500 episodes
- 🧠 SAC agent trains for 500 episodes
- 🧠 Bandit agent trains for ~100 episodes
- 🧠 Each saves checkpoints when improving
- 🧹 Weaker checkpoints are deleted
- 📈 Training summary is printed

### Step 3: Verify Checkpoints Created

```bash
# Using the checkpoint manager
python -c "
from utils.checkpoint_manager import print_checkpoint_summary
print_checkpoint_summary()
"

# Or directly inspect the directory
ls -lh models/rl_checkpoints/
```

Expected output:

```
ppo_20260326161556_reward45.320.pt       (8.4 MB)
sac_20260326165010_reward32.100.pt       (9.2 MB)
bandit_20260326170000_reward78.900.pt    (0.5 MB)
```

### Step 4: Evaluate Each Model

```bash
# Evaluate PPO on test data
python eval_agent.py --agent_type ppo

# Evaluate SAC
python eval_agent.py --agent_type sac

# Evaluate Bandit
python eval_agent.py --agent_type bandit
```

### Step 5: Compare Performance

```bash
# Show detailed comparison
python -c "
from utils.checkpoint_manager import list_checkpoints
import json

checkpoints = list_checkpoints()
print('MODEL PERFORMANCE COMPARISON:')
print('=' * 60)

best_overall = {}
for agent_type, ckpts in checkpoints.items():
    if ckpts:
        best = ckpts[0]  # Already sorted by reward
        best_overall[agent_type] = best['reward_score']
        print(f'{agent_type.upper():10s}: {best[\"reward_score\"]:8.3f} ({best[\"filename\"]})')

print('=' * 60)
print(f'BEST OVERALL: {max(best_overall, key=best_overall.get).upper()}')
"
```

### Step 6: Deploy Best Model

```bash
# Get the best PPO checkpoint path
python -c "
from utils.checkpoint_manager import find_best_checkpoint
best = find_best_checkpoint('ppo')
print(f'Best PPO checkpoint: {best}')
"

# Copy to production
cp models/rl_checkpoints/ppo_*.pt models/rl_checkpoints/ppo_production.pt

# Or in pricing API, it automatically uses find_best_checkpoint()
```

---

## Monitoring Training Progress

### View Real-Time Training Output

```bash
# Run with output to terminal
python train_all_models.py --agents ppo --episodes 500 2>&1 | tee training.log

# Then monitor
tail -f training.log
```

### Check Training Metrics

During training, each agent logs:

- Episode number
- reward earned
- Average loss
- Policy improvements
- Checkpoint saves

Example log output:

```
[INFO] Episode   50/500 | Reward: 32.120 | Avg Loss: 0.234
[INFO] Episode  100/500 | Reward: 38.450 | Avg Loss: 0.189 | ✓ New best!
[INFO] Episode  150/500 | Reward: 42.100 | Avg Loss: 0.156 | ✓ New best!
[INFO] Saved checkpoint: PPO_20260326_reward42.100.pt
```

---

## Best Practices

### 1. Always Use Unified Training

```bash
# ✅ Good: Uses orchestrator with checkpoint management
python train_all_models.py --agents ppo sac bandit

# ❌ Avoid: Manual training of individual agents
python train_agent.py  # No cleanup, hard to track best
```

### 2. Set Appropriate Episode Counts

| Agent  | Episodes | Reason                                |
| ------ | -------- | ------------------------------------- |
| PPO    | 500-2000 | Converges slowly, needs many episodes |
| SAC    | 500-2000 | Off-policy, explores more             |
| Bandit | 50-200   | Converges fast, discrete arms         |

```bash
# Good configuration
python train_all_models.py --episodes 1000 --agents ppo sac --episodes 100 --agents bandit
```

### 3. Monitor Checkpoint Growth

```bash
# Check disk usage
du -sh models/rl_checkpoints/

# Keep disk usage under control
python train_all_models.py --keep-top 3  # Keep only 3 best per agent
```

### 4. Never Delete Checkpoint Manually

```bash
# ❌ Bad
rm models/rl_checkpoints/ppo_*.pt

# ✅ Good
python -c "from utils.checkpoint_manager import cleanup_all_weaker_checkpoints; cleanup_all_weaker_checkpoints(keep_top_n=1)"
```

### 5. Before Production Deployment

```bash
# Step 1: Train
python train_all_models.py --agents ppo sac bandit --episodes 500

# Step 2: Evaluate all three
python eval_agent.py --agent_type ppo
python eval_agent.py --agent_type sac
python eval_agent.py --agent_type bandit

# Step 3: Compare results and choose best
python -c "
from utils.checkpoint_manager import list_checkpoints
checkpoints = list_checkpoints()
for agent, ckpts in checkpoints.items():
    best = ckpts[0]
    print(f'{agent}: {best[\"reward_score\"]:.3f}')
"

# Step 4: Update API to use best model
# Edit backend/api/routes/prices.py to load best checkpoint
```

---

## Troubleshooting

### Issue: "No checkpoints found"

```bash
# Check if checkpoints directory exists
ls -la backend/models/rl_checkpoints/

# If empty, make sure training completed
python train_all_models.py --agents ppo --episodes 100

# Check logs
tail backend/training_orchestrator.log
```

### Issue: Training too slow

```bash
# Use fewer episodes for testing
python train_all_models.py --episodes 50

# Or train specific agent that needs improvement
python train_all_models.py --agents ppo --episodes 100
```

### Issue: Checkpoints getting too large

```bash
# Keep fewer checkpoints
python train_all_models.py --keep-top 1  # Only keep best

# Or cleanup existing
python -c "
from utils.checkpoint_manager import cleanup_all_weaker_checkpoints
cleanup_all_weaker_checkpoints(keep_top_n=1)
print('Cleanup complete')
"
```

### Issue: Different rewards each time

This is expected! RL agents are stochastic:

- Initialize networks randomly
- Sample experiences randomly
- Use entropy regularization

Solution: Train multiple times and take the best:

```bash
# Run 3 times and keep best checkpoint overall
for i in {1..3}; do
  python train_all_models.py --agents ppo --episodes 500
done

python -c "
from utils.checkpoint_manager import find_best_checkpoint
best = find_best_checkpoint('ppo')
print(f'Best PPO: {best}')
"
```

---

## Integration with API

### Using Best Checkpoint in API

Edit `backend/api/routes/prices.py`:

```python
from utils.checkpoint_manager import find_best_checkpoint

@router.get("/recommend/{product_id}")
async def recommend_price(product_id: str, agent_type: str = "ppo"):
    """Get price recommendation from best trained model."""

    # Automatically find best checkpoint
    best_ckpt = find_best_checkpoint(agent_type)

    if not best_ckpt:
        raise HTTPException(status_code=500, detail=f"No trained checkpoint for {agent_type}")

    # Load agent with best checkpoint
    agent = load_agent(agent_type, best_ckpt)

    # Get recommendation
    price = agent.recommend_price(product_id)
    return {"product_id": product_id, "recommended_price": price}
```

### Testing API with Trained Models

```bash
# Make sure API server is running
python main.py &

# Test with PPO
curl "http://localhost:8000/api/prices/recommend/PROD-001?agent_type=ppo"

# Test with SAC
curl "http://localhost:8000/api/prices/recommend/PROD-001?agent_type=sac"

# Test with Bandit
curl "http://localhost:8000/api/prices/recommend/PROD-001?agent_type=bandit"
```

---

## Summary Table

| Task             | Command                                 | Purpose                      |
| ---------------- | --------------------------------------- | ---------------------------- |
| Train all        | `python train_all_models.py`            | Train PPO, SAC, Bandit       |
| View checkpoints | `print_checkpoint_summary()`            | Show all available models    |
| Find best        | `find_best_checkpoint("ppo")`           | Get best PPO checkpoint      |
| Cleanup          | `cleanup_all_weaker_checkpoints(3)`     | Keep only top 3 per agent    |
| Evaluate         | `python eval_agent.py --agent_type ppo` | Get metrics on test data     |
| Deploy           | Use `find_best_checkpoint()` in API     | Use best model in production |

---

## Next Steps

1. ✅ **Run training orchestrator** to train all three models
2. ✅ **Evaluate each model** to see which performs best
3. ✅ **Check checkpoint summary** to verify cleanup worked
4. ✅ **Update API** to use `find_best_checkpoint()`
5. ✅ **Test in POS terminal** with all three agents
6. ✅ **Deploy best model** to production

---

**Happy training! 🚀**
