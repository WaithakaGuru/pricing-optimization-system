# 🚀 Quick Reference: Model Training & Checkpoints

## TL;DR - Quick Commands

```bash
# Train all three models in one command
python train_all_models.py --agents ppo sac bandit --episodes 500 --cleanup

# Check checkpoint status
python checkpoints_status.py

# Compare best models
python checkpoints_status.py --compare

# Cleanup weaker checkpoints
python checkpoints_status.py --cleanup --keep-top 3
```

---

## The System Works Like This

### 1️⃣ **Training Phase**

```
┌─────────────────────────────────────────────────────────┐
│ python train_all_models.py --agents ppo sac bandit      │
│                                                         │
│ ✅ Trains PPO                                           │
│    └─ Saves: ppo_20260326161556_reward45.320.pt       │
│                                                         │
│ ✅ Trains SAC                                           │
│    └─ Saves: sac_20260326165010_reward32.100.pt       │
│                                                         │
│ ✅ Trains Bandit                                        │
│    └─ Saves: bandit_20260326170000_reward78.900.pt    │
└─────────────────────────────────────────────────────────┘
```

### 2️⃣ **Checkpoint Selection**

- Each checkpoint filename contains the **reward score**
- Higher reward = Better model
- Sorted automatically by performance

### 3️⃣ **Cleanup Phase**

```
Before cleanup (5 checkpoints):
  ❌ ppo_..._reward35.200.pt  (DELETED - weak)
  ❌ ppo_..._reward40.100.pt  (DELETED - weak)
  ✅ ppo_..._reward45.320.pt  (KEPT - best)
  ✅ ppo_..._reward45.100.pt  (KEPT - 2nd best)
  ✅ ppo_..._reward44.890.pt  (KEPT - 3rd best)

After cleanup:
  ✅ ppo_..._reward45.320.pt  (BEST)
  ✅ ppo_..._reward45.100.pt  (2nd best)
  ✅ ppo_..._reward44.890.pt  (3rd best)
```

---

## Essential Commands

### Training

```bash
# Train all three models (recommended)
python train_all_models.py

# Train only specific models
python train_all_models.py --agents ppo sac

# Train with custom episode count
python train_all_models.py --episodes 1000

# Train without cleanup (keep all checkpoints)
python train_all_models.py --no-cleanup
```

### Checkpoint Management

```bash
# View all checkpoints
python checkpoints_status.py

# View only best checkpoint per agent
python checkpoints_status.py --best

# Compare best models side-by-side
python checkpoints_status.py --compare

# Show statistics
python checkpoints_status.py --stats

# Cleanup weaker checkpoints
python checkpoints_status.py --cleanup

# Cleanup and keep only top 5
python checkpoints_status.py --cleanup --keep-top 5

# Generate JSON report
python checkpoints_status.py --report checkpoints.json
```

### Python API Usage

```python
from utils.checkpoint_manager import (
    find_best_checkpoint,
    list_checkpoints,
    cleanup_all_weaker_checkpoints
)

# Get best checkpoint for an agent
best_ppo = find_best_checkpoint("ppo")  # Returns: "/path/to/ppo_...reward45.320.pt"

# List all checkpoints
all_checkpoints = list_checkpoints()
# Returns: {"ppo": [...], "sac": [...], "bandit": [...]}

# Cleanup
cleanup_all_weaker_checkpoints(keep_top_n=3)
```

---

## Typical Workflow

### Day 1: Initial Training

```bash
# 1. Train all models
python train_all_models.py --agents ppo sac bandit --episodes 500

# 2. Check results
python checkpoints_status.py --compare

# Output:
# Rank  Agent      Reward       Best CheckpointSize
# 🥇 1  PPO        45.320       ppo_..._reward45.320.pt
# 🥈 2  BANDIT     78.900       bandit_..._reward78.900.pt
# 🥉 3  SAC        32.100       sac_..._reward32.100.pt
```

### Day 2: Improve Models

```bash
# SAC has lowest reward, retrain it
python train_all_models.py --agents sac --episodes 500

# Check results again
python checkpoints_status.py --compare

# Now SAC might be better, or keep PPO if still best
```

### Production Deployment

```bash
# Find best PPO checkpoint
python -c "from utils.checkpoint_manager import find_best_checkpoint; print(find_best_checkpoint('ppo'))"

# API automatically uses: find_best_checkpoint(agent_type)
# So it always loads the best available checkpoint
```

---

## How to Choose Best Model

### Option 1: Automatic (Recommended)

```python
# API automatically chooses best
from utils.checkpoint_manager import find_best_checkpoint

@app.get("/recommend/{product_id}")
def recommend(product_id: str, agent_type: str = "ppo"):
    best_ckpt = find_best_checkpoint(agent_type)  # Always latest best!
    return agent.predict(product_id)
```

### Option 2: Manual Comparison

```bash
# Compare all three agents
python checkpoints_status.py --compare

# Choose winner and note its path
# Use that specific checkpoint in API
```

### Option 3: Evaluate on Test Set

```bash
# Evaluate each agent
python eval_agent.py --agent_type ppo
python eval_agent.py --agent_type sac
python eval_agent.py --agent_type bandit

# Compare metrics and choose
```

---

## File Structure

```
backend/
├── models/
│   └── rl_checkpoints/
│       ├── ppo_20260326161556_reward45.320.pt    ⭐ Best PPO
│       ├── ppo_20260326141010_reward44.890.pt
│       ├── sac_20260326165010_reward32.100.pt    ⭐ Best SAC
│       ├── bandit_20260326170000_reward78.900.pt ⭐ Best Bandit
│       └── checkpoint_metadata.json              (metadata tracking)
│
├── train_all_models.py          ← Run this to train all
├── checkpoints_status.py         ← Run this to view status
├── train_agent_synthetic_v2.py   (individual agent trainer)
├── train_bandit.py               (bandit trainer)
└── utils/
    └── checkpoint_manager.py     (checkpoint API)
```

---

## Common Scenarios

### Scenario 1: "I want to train PPO better"

```bash
# Check current best
python checkpoints_status.py --best  # Shows best PPO

# Retrain PPO with more episodes
python train_all_models.py --agents ppo --episodes 1000

# Check if improved
python checkpoints_status.py --best

# Old weak checkpoints auto-deleted (keep top 3)
```

### Scenario 2: "SAC and Bandit perform better than PPO"

```bash
# Compare all
python checkpoints_status.py --compare

# Result: SAC is best, so use SAC in API:
curl "http://localhost:8000/api/prices/recommend/PROD-001?agent_type=sac"

# Or update API to prefer SAC by default
```

### Scenario 3: "Checkpoints folder is too large"

```bash
# Check size
du -sh models/rl_checkpoints/

# Keep only best (top 1) per agent
python checkpoints_status.py --cleanup --keep-top 1

# Check size after cleanup
du -sh models/rl_checkpoints/
```

### Scenario 4: "I want to keep training history"

```bash
# Save current checkpoints before cleanup
cp -r models/rl_checkpoints models/rl_checkpoints_backup_20260326

# Or use --no-cleanup flag
python train_all_models.py --agents ppo --no-cleanup

# Manual cleanup later
python checkpoints_status.py --cleanup
```

---

## Troubleshooting

| Problem                  | Solution                                                   |
| ------------------------ | ---------------------------------------------------------- |
| "No checkpoints found"   | Run: `python train_all_models.py --episodes 100`           |
| "Low reward scores"      | Need to fix reward shaper (see MODEL_TRAINING_ANALYSIS.md) |
| "Training is slow"       | Use fewer episodes: `--episodes 50` for testing            |
| "Checkpoints too large"  | Use `--cleanup --keep-top 1`                               |
| "Want to compare models" | Run: `python checkpoints_status.py --compare`              |
| "Training keeps failing" | Check logs: `tail training_orchestrator.log`               |

---

## Key Functions Reference

### Find Best Checkpoint

```python
from utils.checkpoint_manager import find_best_checkpoint

path = find_best_checkpoint("ppo")
# Returns: "/Users/.../models/rl_checkpoints/ppo_...reward45.320.pt"
```

### List All Checkpoints

```python
from utils.checkpoint_manager import list_checkpoints

checkpoints = list_checkpoints()
# Returns per-agent list, sorted by reward (best first)
```

### Cleanup Weaker Ones

```python
from utils.checkpoint_manager import cleanup_all_weaker_checkpoints

deleted, remaining = cleanup_all_weaker_checkpoints(keep_top_n=3)
print(f"Deleted {deleted}, kept {remaining}")
```

### Print Summary

```python
from utils.checkpoint_manager import print_checkpoint_summary

print_checkpoint_summary()  # Nice formatted output
```

---

## Next Steps

1. ✅ Run: `python train_all_models.py --agents ppo sac bandit --episodes 500`
2. ✅ Check: `python checkpoints_status.py --compare`
3. ✅ Cleanup: `python checkpoints_status.py --cleanup`
4. ✅ Verify best checkpoint is being used in API
5. ✅ Test in POS terminal with recommendations

---

**Happy training! Questions? See MODEL_TRAINING_GUIDE.md for detailed info.** 🚀
