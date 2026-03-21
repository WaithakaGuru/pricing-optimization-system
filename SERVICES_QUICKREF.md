"""Quick reference for running services integration tests and verifying real data flows."""

# ============================================================================

# SERVICES LAYER - QUICK REFERENCE

# ============================================================================

# 1. VIEW DATABASE

# ================

# Option A: Prisma Studio GUI (easiest, if Prisma configured)

# $ npm run studio

# Option B: SQLite Browser App (recommended GUI)

# Download: https://sqlitebrowser.org

# Open file: backend/optima.db

# Option C: Python + Pandas (analysis)

# $ python backend/view_db.py

# Option D: SQLite CLI (production debugging)

# $ sqlite3 backend/optima.db

# > SELECT \* FROM Product LIMIT 5;

# > .tables

# See DATABASE_VIEWING_GUIDE.md for detailed instructions

# 2. RUN SERVICES INTEGRATION TEST

# ==================================

# Tests real data flows through all services

# $ cd backend

# $ python test_services_integration.py

#

# Output:

# ✓ WeatherService: Fetches live weather from Open-Meteo

# ✓ InventoryService: Queries database stock levels

# ✓ PricingService: Gets recommendations from agents (PPO/SAC/Bandit)

# 3. SERVICES USAGE PATTERNS

# ============================

# Pattern A: WeatherService (async)

# from services.weather_service import WeatherService

# import asyncio

#

# async def get_weather():

# weather = WeatherService(latitude=40.7128, longitude=-74.0060) # NYC

# current = await weather.get_current_weather()

# normalized = await weather.get_weather_for_state()

# await weather.close()

# return current, normalized

#

# current, normalized = asyncio.run(get_weather())

# Pattern B: InventoryService (sync)

# from services.inventory_service import InventoryService

#

# inv_service = InventoryService()

# inventory = inv_service.get_inventory("PROD-001")

# turnover = inv_service.get_turnover_rate("PROD-001", days=30)

# alerts = inv_service.check_reorder_alerts()

# state_features = inv_service.get_inventory_for_state("PROD-001")

# Pattern C: PricingService (sync) - RECOMMENDED

# from services.pricing_service import PricingService

#

# # Initialize with trained agent

# pricing = PricingService(agent_type="ppo", checkpoint_path="models/ppo_checkpoint.pt")

#

# # Get recommendation

# rec = pricing.get_recommendation("PROD-001")

# # Returns:

# # {

# # "product_id": "PROD-001",

# # "current_price": 15.99,

# # "recommended_price": 18.50,

# # "agent": "ppo",

# # "confidence": 0.87,

# # "factors": {

# # "cost_price": 8.00,

# # "margin_pct": 42.5,

# # "inventory_level": 150,

# # "turnover_rate": 5.2,

# # "weeks_in_stock": 2.5,

# # "seasonality": 0.95,

# # "weather_impact": 1.1,

# # "sales_trend": "up"

# # },

# # "timestamp": "2024-03-19T10:30:00Z"

# # }

#

# # Apply recommendation to database

# result = pricing.apply_price("PROD-001", 18.50, applied_by="agent")

#

# # Record transaction (after POS sale)

# pricing.record_transaction("PROD-001", qty=5, price=18.50, revenue=92.50)

# 4. NEXT STEP: API INTEGRATION

# ==============================

# Create FastAPI routes that wrap services:

#

# # backend/api/routes/prices.py

# @router.get("/prices/recommend/{product_id}")

# def recommend_price(product_id: str):

# service = PricingService(agent_type="ppo")

# return service.get_recommendation(product_id)

#

# @router.post("/prices/apply/{product_id}")

# def apply_price(product_id: str, price: float):

# service = PricingService(agent_type="ppo")

# return service.apply_price(product_id, price, applied_by="api")

# 5. DATA FLOW DIAGRAM

# =====================

#

# Product Sales (POS)

# ↓

# PricingService.record_transaction()

# ↓

# Database (Transaction, PriceHistory)

# ↓

# Next Decision:

# • InventoryService: Queries stock levels, turnover rates

# • WeatherService: Fetches real weather data

# • StateBuilder: Assembles 12-dim state vector

# • Agent (PPO/SAC/Bandit): Recommends new price

# • PricingService.apply_price(): Update database

# ↓

# New Price Applied

# ↓

# Feedback Loop for Agent Learning

# 6. AGENT SELECTION

# ===================

# All services support interchangeable agent types:

#

# "ppo": Stable policy gradient (recommended for production)

# "sac": Off-policy entropy-regularized (high sample efficiency)

# "bandit": Fast discrete learner (low latency, fast adaptation)

# 7. TROUBLESHOOTING

# ===================

#

# Issue: "Database locked" error

# Fix: Close other SQLite connections (browser, Python shell, etc.)

#

# Issue: "Weather API timeout"

# Fix: Check internet connection; Open-Meteo has high availability

#

# Issue: "Agent checkpoint not found"

# Fix: Train agent first with train_bandit.py or similar

#

# Issue: "Product not found in database"

# Fix: Run init_db.py to create sample products

# 8. MONITORING

# ==============

# View database while running services:

#

# Terminal 1: $ python test_services_integration.py

# Terminal 2: $ while true; do python backend/view_db.py inventory; sleep 5; done

#

# Watch inventory, prices, and transactions update in real-time

if **name** == "**main**":
print(**doc**)
