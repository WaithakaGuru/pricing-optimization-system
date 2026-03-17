# Price Optimizer Backend Structure

Complete backend scaffolding for ML-Powered Dynamic Price Optimization Engine.

## 📁 Directory Structure

The backend is organized into the following modules:

### `api/` — FastAPI Application

- **routes/** — API endpoint routes
  - `prices.py` — Price recommendation endpoints
  - `inventory.py` — Inventory management endpoints
  - `pos.py` — POS transaction endpoints
  - `agent.py` — RL agent control endpoints
- **middleware/** — CORS, auth, error handling
- **main.py** — FastAPI app factory and initialization

### `services/` — Business Logic

- `pricing_service.py` — Price recommendations and management
- `inventory_service.py` — Inventory tracking and alerts
- `weather_service.py` — External weather data integration

### `schemas/` — Data Models

- `models.py` — Pydantic request/response schemas

### Backend — ORM Models

- `models.py` — SQLAlchemy database models for:
  - Products, Inventory, Transactions, Price History, Agent Metrics

---

## 🧠 RL Engine (`../rl/`)

### `agents/` — Agent Implementations

- `bandit.py` — Phase 1: Contextual bandit (quick bootstrap)
- `ppo_agent.py` — Phase 2: PPO policy gradient
- `sac_agent.py` — Phase 2 Alt: SAC (continuous actions)

### `environment/` — Gym-Compatible Environment

- `price_env.py` — Custom PriceOptimizationEnv (state, action, reward)
- `state_builder.py` — Assembles state from all signals
- `reward_shaper.py` — Designs reward function (critical!)

### `networks/` — Neural Networks

- `actor.py` — Policy network (maps state → action)
- `critic.py` — Value network (maps state → value)

### `trainer.py` — Training Loop

Handles episode collection, batch updates, checkpointing, and metric logging.

---

## 🤖 ML Support (`../ml/`)

### `demand_forecasting/`

- `prophet_model.py` — Time series forecasting (seasonality decomposition)
- `train.py` — Training script

### `elasticity/`

- `xgboost_model.py` — Price elasticity model (demand ~ price + features)
- `train.py` — Training script

### `anomaly/`

- `detector.py` — Detects unusual pricing/demand patterns

---

## 📊 Data Layer (`../data/`)

### Structure

- `raw/` — Ingested raw data
- `processed/` — Feature-engineered datasets
- `synthetic/` — Generated bootstrap data (no real data needed initially)
- `loaders/`
  - `weather_loader.py` — Open-Meteo API integration
  - `trends_loader.py` — Google Trends integration

---

## ⚙️ Configuration & Utilities (`utils/`)

- `config.py` — Central configuration (env vars via pydantic-settings)
- `logger.py` — Structured logging
- `synthetic_data.py` — Generate bootstrap training data
- `metrics.py` — KPI calculation (revenue, margin, velocity)

---

## 🧪 Testing

- `test_env.py` — Environment tests
- `test_reward.py` — Reward function tests
- `test_api.py` — API endpoint tests

Run with: `pytest tests/`

---

## 🐳 Deployment

### Docker Compose

- Services: PostgreSQL, Redis, Backend API, Frontend, Celery Worker
- Start: `docker-compose up -d`
- Stop: `docker-compose down`

### Database

Uses PostgreSQL for production (configure `DATABASE_URL` in `.env`)
SQLite for local development

### Caching & Task Queue

- Redis for caching and Celery task queue
- Celery Beat for scheduled retraining

---

## 📋 Getting Started

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Initialize database** (when ready):

   ```bash
   # Use Alembic for migrations (to be set up)
   alembic upgrade head
   ```

4. **Run locally**:

   ```bash
   python main.py
   # API will be at http://localhost:8000
   # Docs at http://localhost:8000/docs
   ```

5. **Or with Docker**:
   ```bash
   docker-compose up
   ```

---

## 🔑 Key Implementation Priorities

1. **State Builder** (`rl/environment/state_builder.py`)
   - Fetches product, inventory, demand, weather, trends
   - Normalizes all features to reasonable scale
   - Returns state vector for RL agent

2. **Reward Shaper** (`rl/environment/reward_shaper.py`)
   - **Critical**: Quality of reward = quality of learned policy
   - Balance: revenue ↑, inventory turnover ↑, price stability, margin safety

3. **Demand Forecaster** (`ml/demand_forecasting/prophet_model.py`)
   - Captures seasonality, trends, holidays
   - Feeds into state and reward calculation

4. **Elasticity Model** (`ml/elasticity/xgboost_model.py`)
   - Predicts demand at different prices
   - Prerequisite for reward calculation

5. **Training Loop** (`rl/trainer.py`)
   - Orchestrates environment, agent updates, checkpointing
   - Integration with Weights & Biases or MLflow

---

## 📚 Tech Stack

- **API**: FastAPI + Uvicorn
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Cache**: Redis
- **Tasks**: Celery + Celery Beat
- **RL**: Gymnasium + PyTorch + Stable-Baselines3
- **ML**: Prophet + XGBoost + scikit-learn
- **Monitoring**: Weights & Biases or MLflow
- **Testing**: pytest

---

Next Steps:

1. Implement `StateBuilder` to assemble RL state
2. Design reward function in `RewardShaper`
3. Train demand forecaster with sample data
4. Run contextual bandit (Phase 1) to bootstrap pricing
5. Transition to PPO/SAC (Phase 2) after warm start
