# Optima - Progress Tracker

## 📋 Project Overview

ML-Powered Dynamic Price Optimization Engine using Reinforcement Learning to optimize prices based on demand, inventory, weather, and market trends.

---

## ✅ Completed

### Phase 1: Project Setup

- [x] Created complete backend folder structure
- [x] Set up conda environment (`pricing`)
- [x] Installed core dependencies (FastAPI, SQLAlchemy, Pydantic, etc.)
- [x] Created SQLite database with 5 tables:
  - Product
  - InventoryItem
  - Transaction
  - PriceHistory
  - AgentMetrics
- [x] Built FastAPI application with 4 route modules (prices, inventory, POS, agent)
- [x] Tested API endpoints work correctly

### Phase 2: Infrastructure

- [x] Created directory structure for RL, ML, data, utils, tests
- [x] Set up ORM models (SQLAlchemy)
- [x] Created Pydantic schemas for API validation

---

## 🚀 In Progress & Completed

### Phase 3: Core Logic Implementation

#### ✅ StateBuilder - COMPLETED

**What it does**: Assembles a 12-dimensional state vector for the RL agent:

- **Product Features**: current price, cost price, margin %
- **Inventory Signals**: inventory level, turnover rate
- **Demand Signals**: sales velocity (7-day, 30-day), demand trend
- **Market Signals**: price trend, seasonality, weather, competitor factor

**How it works**:

1. Fetches product & inventory from database
2. Calculates sales velocity and turnover from transactions
3. Derives trends and seasonality
4. Normalizes all features to [0, 1] range
5. Returns numpy array (shape: 12,) ready for RL agent

**Example Usage**:

```python
from rl.environment.state_builder import StateBuilder
state_builder = StateBuilder()
state = state_builder.build_state("PRODUCT-001")  # Returns normalized 12-dim vector
```

**Test it**: `python test_state_builder.py`.

---

#### ✅ RewardShaper - COMPLETED

**What it does**: Designs the reward function that teaches the RL agent what behaviors we want.

**4 Components Balanced**:

1. **Revenue Reward** — Maximize profit per transaction
2. **Margin Bonus** — Ensure margin stays above 20% (unsustainable to go lower)
3. **Inventory Penalty** — Penalize excess stock (penalizes if >30 days of inventory)
4. **Stability Penalty** — Discourage erratic price changes (max 10% change allowed)

**How it works**:

- Takes state, price action, and observed outcome
- Computes 4 reward components independently
- Weights them (revenue_weight=1.0, margin_weight=0.3, inventory_weight=0.5, stability_weight=0.2)
- Returns normalized reward in [-1, 1] range
- Agent learns to maximize these rewards

**Example Outcomes**:

- Good pricing + good sales = **+0.8 reward** ✓
- Price drop + excess inventory = **-0.9 reward** ✗
- Bad margin (below 20%) = **-1.0 penalty** ✗
- Optimal balanced pricing = **+0.95 reward** ✓✓

**Example Usage**:

```python
from rl.environment.reward_shaper import RewardShaper

shaper = RewardShaper(config={
    "min_margin_pct": 20,
    "max_inventory_days": 30,
})

state = {"current_price": 10.0, "cost_price": 6.0, "inventory_level": 100}
action = 11.0  # Set price to $11
next_state = {"quantity_sold": 80, "inventory_level": 20, "cost_price": 6.0}

reward = shaper.compute_reward(state, action, next_state, debug=True)
breakdown = shaper.get_reward_breakdown()
```

---

#### ✅ Synthetic Data Generator - COMPLETED

**What it does**: Creates realistic but fake training data without needing real customer data.

**Generates**:

1. **Sales Data** — Realistic transactions with price elasticity
   - Demand model: `quantity = base × (price/base_price)^elasticity + noise + seasonality`
   - Elasticity: -0.5 (typical retail)
   - Random daily fluctuations
   - Realistic revenue/cost/profit

2. **Inventory Data** — Stock movements with restocking
   - Stock depletion matching demand
   - Automatic restocking at reorder points
   - Tracks restock events

3. **Weather Data** — Seasonal weather patterns
   - Temperature seasonality
   - Humidity, precipitation, cloud cover
   - Realistic daily and yearly cycles

4. **Product Master** — Product metadata
   - Base prices, cost prices
   - Min/max price bounds
   - Categories

**Test it**: `python test_synthetic_data.py`

---

#### ✅ RL Environment (PriceOptimizationEnv) - COMPLETED

**What it does**: Gymnasium-compatible environment that ties StateBuilder, RewardShaper, and demand simulation together.

**Core Workflow**:

1. **Reset**: Initialize environment with a product
2. **Step**: Agent proposes a price → Environment:
   - Simulates customer demand (using price elasticity)
   - Updates inventory
   - Computes reward (using RewardShaper)
   - Returns new state (from StateBuilder)
3. **Repeat**: Agent learns from reward feedback

**Test it**: `python test_env_integration.py`

---

#### ✅ Phase 1 Agent: Contextual Bandit - COMPLETED

**What it does**: Fast learning agent for discrete price selection using exploration-exploitation tradeoff.

**Two Algorithms**:

1. **Upper Confidence Bound (UCB)**
   - Tracks mean reward and pull count per price arm
   - Selects arm with highest: `mean_reward + sqrt(ln(total_pulls) / arm_pulls)`
   - Naturally balances exploration (pulling uncertain arms) vs exploitation (pulling best arms)
   - Stateless: learns without context

2. **Thompson Sampling**
   - Models each price as Beta distribution of success/failure
   - Samples from posterior distribution each step
   - Optimistic sampling: explores high-variance arms cautiously
   - More sophisticated but still fast learner

**Features**:

- Discrete price action space (10-50 price points)
- Configurable price ranges ($0.10 to $1000)
- Epsilon-greedy fallback for exploration
- Statistics tracking: pull counts, rewards per price, convergence analysis

**How it learns**:

1. Environment selects a price for product
2. Demand simulation runs (elasticity model)
3. RewardShaper evaluates the outcome
4. Bandit updates statistics for that price arm
5. Next step: selects price most rewarded so far (with exploration bonus)

**Example Usage**:

```python
from rl.agents.bandit import ContextualBandit
from rl.environment.price_env import PriceOptimizationEnv

# Initialize bandit with 20 discrete price points
bandit = ContextualBandit(
    n_arms=20,
    n_features=12,
    algorithm="ucb",  # or "thompson"
    price_min=5.0,
    price_max=50.0
)

# Create environment
env = PriceOptimizationEnv(product_id="PRODUCT-001")

# Training loop
for episode in range(100):
    state, info = env.reset()
    for step in range(100):
        arm = bandit.select_arm(state, epsilon=0.1)  # UCB or Thompson
        price = bandit.prices[arm]

        state, reward, done, truncated, info = env.step(price)
        bandit.update(arm, reward)

        if done or truncated:
            break
```

**Train it**: `python train_bandit.py` (100 episodes, detailed statistics)
**Test it**: `python test_bandit_simple.py` (quick validation with simulated rewards)

---

#### ✅ Phase 2 Agents - COMPLETED

##### ✅ PPO Agent (Proximal Policy Optimization)

**What it does**: Full policy gradient RL agent for continuous price optimization.

**Why PPO?**

- Stable policy gradient with clipping to prevent large updates
- Sample-efficient: reuses experience via mini-batch SGD
- Natural fit for continuous action spaces (smooth prices)
- More reliable convergence than vanilla policy gradient

**Architecture**:

- **Input**: 12-dim state from StateBuilder
- **Policy Network (Actor)**: Outputs Gaussian distribution over prices
- **Value Network (Critic)**: Estimates expected return
- **Action Space**: Continuous prices [0.1, 1000]

**Key Components**:

- `select_action()`: Sample action from policy (or deterministic)
- `store_experience()`: Buffer states, actions, rewards, log-probs, values
- `update()`: PPO update with clipping, advantage estimation (GAE), and gradient descent

**Hyperparameters**:

- `clip_ratio`: PPO epsilon (0.2 default - limits policy update size)
- `entropy_coef`: Entropy bonus for exploration (0.01)
- `gamma`: Discount factor (0.99)
- `gae_lambda`: GAE coefficient (0.95 - bias/variance tradeoff)
- `n_epochs`: Epochs of mini-batch training (10)

**Files**:

- [rl/agents/ppo_agent.py](backend/rl/agents/ppo_agent.py) - Full implementation
- [test_ppo_agent.py](backend/test_ppo_agent.py) - Unit tests

**Example Usage**:

```python
from rl.agents.ppo_agent import PPOAgent
from rl.environment.price_env import PriceOptimizationEnv

agent = PPOAgent(state_dim=12, action_dim=1, hidden_dim=128)
env = PriceOptimizationEnv(product_id="PROD-001")

state, info = env.reset()
for step in range(100):
    action, log_prob, value = agent.select_action(state)
    next_state, reward, done, truncated, info = env.step(action)
    agent.store_experience(state, action, reward, log_prob, value, done)
    state = next_state
    if done or truncated:
        break

# Update policy after episode
agent.update()
# Save checkpoint
agent.save_checkpoint("models/ppo_model.pt")
```

---

##### ✅ SAC Agent (Soft Actor-Critic)

**What it does**: Off-policy entropy-regularized RL agent for continuous price optimization.

**Why SAC?**

- **Off-policy**: Can reuse past experience (higher sample efficiency)
- **Entropy regularized**: Encourages exploration + prevents premature convergence
- **Stable**: Two Q-networks reduce overestimation bias
- **Automatic temperature tuning**: Balances exploration vs exploitation automatically

**Architecture**:

- **Policy Network (Actor)**: Gaussian policy outputting price distribution
- **Two Q-Networks (Critics)**: Estimate state-action values (reduce bias via min)
- **Target Networks**: Soft-updated for stability
- **Temperature Parameter**: Auto-tuned entropy coefficient

**Key Components**:

- `select_action()`: Sample from policy or deterministic (inference)
- `store_experience()`: Replay buffer for off-policy learning
- `update()`: Q-network update, actor update, temperature update, soft target updates
- `_soft_update_target_networks()`: Gradual target network updates (tau=0.005)

**Hyperparameters**:

- `gamma`: Discount factor (0.99)
- `tau`: Soft update coefficient (0.005 - small = slow updates)
- `entropy_coef`: Initial entropy coefficient (0.2)
- `entropy_target`: Target entropy (auto-tuning reference)
- `buffer_size`: Replay buffer capacity (100K)

**Files**:

- [rl/agents/sac_agent.py](backend/rl/agents/sac_agent.py) - Full implementation
- [test_sac_agent.py](backend/test_sac_agent.py) - Unit tests

**Example Usage**:

```python
from rl.agents.sac_agent import SACAgent
from rl.environment.price_env import PriceOptimizationEnv

agent = SACAgent(state_dim=12, action_dim=1, hidden_dim=128)
env = PriceOptimizationEnv(product_id="PROD-001", max_steps=500)

state, info = env.reset()
for step in range(500):
    # Exploration: sample from policy
    action, _ = agent.select_action(state, deterministic=False)
    next_state, reward, done, truncated, info = env.step(action)

    # Store for replay buffer
    agent.store_experience(state, action, reward, next_state, done)

    # Update with batch from replay buffer (off-policy)
    if len(agent.replay_buffer) > agent.batch_size:
        agent.update(n_updates=1)

    state = next_state
    if done or truncated:
        break

# Save checkpoint
agent.save_checkpoint("models/sac_model.pt")
```

---

##### ✅ RLTrainer - Training Orchestration

**What it does**: Manages training loop, metrics tracking, checkpointing, and evaluation.

**Responsibilities**:

- Runs training episodes in PriceOptimizationEnv
- Collects experience and batches for agent updates
- Handles agent updates (PPO or SAC compatible)
- Logs metrics: episode rewards, policy losses, KPIs
- Evaluates agent performance on test episodes
- Saves checkpoints (periodic + best)
- Tracks training history (JSON logs)

**Features**:

- Configurable episode count, steps per episode, update frequency
- Periodic evaluation (separate eval episodes)
- Best model checkpoint saving
- Training history and metrics export
- Training progress visualization (matplotlib optional)

**Files**:

- [rl/trainer.py](backend/rl/trainer.py) - Full implementation

**Example Usage**:

```python
from rl.agents.ppo_agent import PPOAgent
from rl.environment.price_env import PriceOptimizationEnv
from rl.trainer import RLTrainer

agent = PPOAgent(state_dim=12, action_dim=1)
env = PriceOptimizationEnv(product_id="PROD-001", max_steps=252)

config = {
    "num_episodes": 100,
    "max_steps_per_episode": 252,
    "update_frequency": 5,
    "eval_frequency": 10,
    "checkpoint_frequency": 20,
}

trainer = RLTrainer(agent, env, config=config)
trainer.train(num_episodes=100)

# Get results
summary = trainer.get_results_summary()
print(f"Best reward: {summary['best_episode_reward']}")

# Plot progress
trainer.plot_training_progress("training_progress.png")
```

---

##### ✅ Neural Networks

**Actor Network** ([rl/networks/actor.py](backend/rl/networks/actor.py)):

- Maps state → action distribution (mean, log_std)
- Reparameterization trick for gradient flow
- Supports deterministic (mean only) and stochastic (sampled) actions

**Critic Network** ([rl/networks/critic.py](backend/rl/networks/critic.py)):

- Maps state → value estimate (scalar)
- Provides baseline for advantage estimation

---

##### ✅ Benchmarking

**Compare Phase 1 vs Phase 2** ([test_phase2_benchmark.py](backend/test_phase2_benchmark.py)):

Runs side-by-side comparison:

- Contextual Bandit (Phase 1 baseline)
- PPO (Phase 2)
- SAC (Phase 2 alternative)

Metrics:

- Mean episode reward
- Best/worst episode reward
- Learning stability
- Sample efficiency

---

## ⏳ Next Steps (In Priority Order)

1. ~~**RewardShaper**~~ ✓
2. ~~**Synthetic Data Generator**~~ ✓
3. ~~**RL Environment**~~ ✓
4. ~~**Phase 1 Agent: Contextual Bandit**~~ ✓
5. ~~**Phase 2 Agents: PPO & SAC**~~ ✓

6. **API Integration** — Wire up endpoints:
   - `/api/prices/recommend/{product_id}` — Get price from trained bandit/agent
   - `/api/prices/update-price/{product_id}` — Update price and trigger agent feedback
   - `/api/metrics/dashboard` — Visualization of agent performance

7. **Frontend Integration** — Real-time pricing dashboard:
   - Display current prices & recommendations
   - Show reward metrics and learning progress
   - Manual override controls

8. **Demand Forecaster** (Optional) — Prophet for demand prediction

---

## 📊 Current Status

**Backend**: RL Pipeline Complete! ✓  
**Database**: SQLite + Synthetic Data ✓  
**Core RL Loop**: StateBuilder ✓ → RewardShaper ✓ → Environment ✓ → Bandit Agent ✓
**Phase 1 Agent**: Contextual Bandit Ready for Training ✓
**Next**: Train bandit / Phase 2 PPO+SAC Agents / API Integration
