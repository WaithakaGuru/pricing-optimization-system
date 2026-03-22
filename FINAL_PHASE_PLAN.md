# 🚀 Final Phase Plan: RL Training, Weather Integration & Productionization

**Status**: Phase 1-3 Complete ✅ → Phase 4 Starting 🎯  
**Date**: March 21, 2026  
**Objective**: Deploy a live, self-improving pricing engine with real-world data integration

---

## 📊 Phase 4: Live Training & Data Integration

### Tier 1: Weather Data Integration (Days 1-2)

#### 1.1 Open-Meteo Weather API Setup

- **Provider**: Open-Meteo (free, no API key required)
- **What to Integrate**:
  - Daily temperature (high/low)
  - Precipitation probability
  - Weather conditions (clear, rainy, cloudy)
  - UV index (for beverages/outdoor products)

#### 1.2 Implementation Tasks

```
□ Create WeatherService in backend/services/weather_service.py
  - Cache weather data (4-hour TTL)
  - Fetch historical & forecast data
  - Normalize weather features [0, 1]

□ Update StateBuilder to include weather factors
  - Current weather vector
  - 7-day weather trend
  - Seasonality adjustment from weather

□ Add weather to API response (GET /api/prices/recommend/{product_id})
  - Include weather_factor in recommendation explanation
  - Show "Weather impact: +/-X% on demand"

□ Create WeatherLoader data pipeline (backend/data/loaders/weather_loader.py)
  - Batch load historical weather for past 90 days
  - Feed into training data
```

#### 1.3 Files to Create/Modify

- **NEW**: `backend/services/weather_service.py` — Weather API client
- **NEW**: `backend/data/loaders/weather_loader.py` — Historical data loader
- **MODIFY**: `backend/rl/environment/state_builder.py` — Add weather features
- **MODIFY**: `backend/api/routes/prices.py` — Include weather in response

---

### Tier 2: RL Agent Live Training (Days 3-4)

#### 2.1 Training Loop Architecture

```
┌─────────────────────────────────────┐
│  POS Transaction Recorded           │ (User makes sale)
│  Event: TXN-20260321210952-c82bdb3c │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  1. Extract State                   │ (What were conditions?)
│     - Product features              │
│     - Inventory level               │
│     - Recent demand (7d velocity)   │
│     - Weather conditions            │
│     - Time of day / seasonality     │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  2. Calculate Reward                │ (How did price perform?)
│     - Revenue achieved              │
│     - Margin maintained             │
│     - Inventory impact              │
│     - Price stability               │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  3. Store (State, Action, Reward)   │ (Buffer for learning)
│     - Replay buffer: 100K samples   │
│     - Prioritize recent experiences │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  4. Agent Update (Nightly)          │ (Learn from experiences)
│     - PPO: Policy gradient update   │
│     - SAC: Off-policy update        │
│     - Compute advantages, log probs │
│     - Backprop & parameter update   │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  5. Model Checkpoint Save           │ (Persist learning)
│     - Save actor/critic weights     │
│     - Log training metrics          │
│     - Version control (v1, v2, v3)  │
└─────────────────────────────────────┘
```

#### 2.2 Implementation Tasks

```python
# backend/rl/trainer.py - Live training loop

class LiveTrainer:
    def __init__(self, agent_type='ppo'):
        self.agent = PPOAgent() or SACAgent()
        self.replay_buffer = ReplayBuffer(capacity=100_000)
        self.update_interval = 50  # Update every 50 transactions

    def on_transaction(self, transaction: dict):
        """Called when POS transaction occurs"""
        # Extract state
        state = self.state_builder.build_state(transaction['product_id'])

        # Get reward
        reward = self.reward_shaper.compute_reward(
            prev_state=self.prev_state,
            action=transaction['price'],
            curr_state=state
        )

        # Store experience
        self.replay_buffer.add({
            'state': state,
            'action': transaction['price'],
            'reward': reward,
            'done': False
        })

        # Update agent periodically
        if len(self.replay_buffer) % self.update_interval == 0:
            batch = self.replay_buffer.sample(batch_size=64)
            self.agent.update(batch)
            self.save_checkpoint()

    def save_checkpoint(self):
        """Persist trained model"""
        path = f"models/rl_checkpoints/agent_v{self.version}.pt"
        self.agent.save_checkpoint(path)
```

#### 2.3 Files to Create/Modify

- **ENHANCE**: `backend/rl/trainer.py` — Add live training loop
- **ENHANCE**: `backend/api/routes/agent.py` — Add training status endpoint
- **NEW**: `backend/rl/replay_buffer.py` — Experience buffer
- **NEW**: `backend/logs/training_metrics.json` — Training history

---

### Tier 3: Data Trends & Historical Patterns (Days 5-6)

#### 3.1 Trends Data Integration

```
□ Create TrendsLoader (backend/data/loaders/trends_loader.py)
  - Fetch Google Trends data for product categories
  - Example: "coffee prices", "coffee demand" trending
  - Normalize to [0, 1] interest index

□ Add Holiday Calendar
  - Use `holidays` library (already in requirements.txt)
  - Mark holiday periods → adjust seasonality factor
  - Example: +15% demand on holidays

□ Correlation Analysis
  - Analyze: "When does weather drive demand?"
  - Store correlations in StateBuilder config
  - Use in reward shaping (penalize counter-trend pricing)
```

#### 3.2 Implementation Tasks

- **NEW**: `backend/data/loaders/trends_loader.py` — Google Trends API
- **NEW**: `backend/data/loaders/holidays_loader.py` — Holiday calendar
- **ENHANCE**: `backend/rl/environment/state_builder.py` — Add trend features
- **NEW**: `backend/utils/correlation_analysis.py` — Feature correlation

---

### Tier 4: Monitoring & Productionization (Days 7-8)

#### 4.1 Training Monitoring Dashboard

```
Metrics to Track:
┌─────────────────────────────────────┐
│  Agent Performance Metrics          │
├─────────────────────────────────────┤
│ ✓ Cumulative Reward (learning curve)│
│ ✓ Avg Margin %                      │
│ ✓ Avg Price per Product             │
│ ✓ Revenue per Day                   │
│ ✓ Policy Update Frequency           │
│ ✓ Exploration vs Exploitation ratio │
│ ✓ Model Version History             │
│ ✓ Checkpoint File Sizes             │
└─────────────────────────────────────┘
```

#### 4.2 Implementation Tasks

- **ENHANCE**: `backend/api/routes/agent.py` — Add training metrics endpoint
- **NEW**: `frontend/src/components/dashboard/AgentMetrics.tsx` — Metrics visualization
- **NEW**: `backend/utils/metrics.py` — Metric computation logic
- **ENHANCE**: `backend/logs/` — Structure training history JSON

#### 4.3 A/B Testing Framework

```
□ A/B Test Infrastructure
  - Split products into groups (control vs treatment)
  - Control: Use current prices
  - Treatment: Use PPO recommendations
  - Measure uplift in revenue/margin

□ Implementation
  - GET /api/prices/recommend/{product_id}?ab_test=true
  - Returns: {"recommendation": {...}, "group": "control|treatment"}
  - Log results for analysis
```

---

## 🎯 Tier 5: Advanced Features (Days 9-10)

### 5.1 Multi-Agent Comparison

```
□ Run PPO vs SAC vs Bandit in parallel
  - Each agent gets 5% of products
  - Track which agent performs best
  - Automatically route high-value products to best performer
```

### 5.2 Demand Forecasting Integration

```
□ Prophet Model for Demand Prediction
  - Forecast next 7-day demand for each product
  - Feed into state (predicted_demand_7d feature)
  - Allow agent to pre-optimize for predicted demand spike
```

### 5.3 Competitor Price Integration

```
□ Scrape competitor prices (ethical bounds)
  - Use web scraping library: BeautifulSoup4 + Selenium
  - Cache prices (4-hour TTL)
  - Add competitor_price feature to state
  - Reward: Don't price too high vs competitors
```

---

## 📋 Summary: Week-by-Week Execution Plan

| Week       | Focus                      | Estimated Hours | Files/Tasks                                |
| ---------- | -------------------------- | --------------- | ------------------------------------------ |
| **Week 1** | Weather API + State Update | 16              | WeatherService, StateBuilder enhancement   |
| **Week 1** | Live Training Loop         | 12              | trainer.py, replay_buffer.py, agent routes |
| **Week 2** | Trends & Historical Data   | 12              | TrendsLoader, HolidaysLoader, correlation  |
| **Week 2** | Monitoring Dashboard       | 10              | AgentMetrics routes, Frontend components   |
| **Week 3** | A/B Testing Framework      | 8               | AB test routes, result logging             |
| **Week 3** | Advanced Features          | 12              | Multi-agent, Prophet, Competitor scraping  |
|            | **TOTAL**                  | **70 hours**    | Full productionization ✅                  |

---

## 🔧 Technical Checklist

### Before Starting Training

- [ ] Database backup (copy `pricing.db`)
- [ ] Test StateBuilder with weather data
- [ ] Verify RewardShaper gives reasonable rewards (not saturated)
- [ ] Set up Tensorboard/MLflow for tracking
- [ ] Create test dataset (100 synthetic transactions)
- [ ] Verify API response times < 100ms

### During Live Training

- [ ] Monitor agent loss (should decrease)
- [ ] Monitor policy entropy (should remain moderate)
- [ ] Check for NaN/Inf in gradients
- [ ] Save checkpoints every 500 transactions
- [ ] Weekly model comparison (old vs new)
- [ ] Track revenue impact (with confidence intervals)

### Quality Assurance

- [ ] Unit tests for training loop
- [ ] Integration tests (full pipeline)
- [ ] Load test: 1000 TPS transaction logging
- [ ] Model inference latency test (< 50ms)
- [ ] Cold boot test (load checkpoint + first recommendation)

---

## 🎁 Bonus Improvements (Optional)

```
□ Celery Beat: Run training jobs every night (off-peak)
□ Redis: Cache state computations (300s TTL)
□ MLflow: Centralized experiment tracking
□ Gradio: Simple UI for manual price tweaking
□ ONNX Export: Run models in production without PyTorch
□ Confidence Intervals: Show +/- on recommendations
□ Feature Importance: SHAP values for explanability
□ Rate Limiting: Prevent API abuse
```

---

## 🚨 Success Metrics (Phase 4 Complete)

✅ **Training**

- Agent training loop running live on transactions
- Model improving (reward curve trending up)
- New checkpoints saved daily

✅ **Data**

- Weather data feeding into recommendations
- Trends seasonality captured
- Historical patterns integrated

✅ **Monitoring**

- Real-time training metrics visible in dashboard
- Revenue impact measurable (A/B test)
- Agent decisions explainable

✅ **Robustness**

- System handles 1000 TPS
- Models load in < 50ms
- No data loss (complete transaction logging)

---

## 📞 Questions Before Starting?

1. **Data**: Do you have real transaction history to backfill, or start with synthetic?
2. **Budget**: Any external APIs we should avoid? (e.g., paid weather providers?)
3. **Timeline**: Need Phase 4 complete by specific date?
4. **Hardware**: Training on CPU or have GPU available?
5. **Monitoring**: Preference for MLflow vs Tensorboard vs Weights & Biases?

**Ready to proceed? Let me know which tier to start with! 🎯**
