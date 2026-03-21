# API Integration - Complete Reference

All services are now integrated with FastAPI endpoints. The backend is ready for frontend integration.

---

## 🚀 Start the API Server

```bash
cd backend
python main.py
```

API will be available at: `http://localhost:8000`
Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## 📊 API Endpoints by Category

### **1. PRICES** — Dynamic pricing recommendations and management

#### Get Price Recommendation

```http
GET /api/prices/recommend/{product_id}?agent_type=ppo
```

**Query Parameters:**

- `agent_type`: `ppo` (default), `sac`, or `bandit`

**Response:**

```json
{
  "product_id": "PROD-001",
  "current_price": 15.99,
  "recommended_price": 18.5,
  "confidence": 0.87,
  "agent": "ppo",
  "factors": {
    "cost_price": 8.0,
    "margin_pct": 42.5,
    "inventory_level": 150,
    "turnover_rate": 5.2,
    "seasonality": 0.95,
    "weather_impact": 1.1,
    "sales_trend": "up"
  },
  "timestamp": "2024-03-19T10:30:00Z"
}
```

#### Get Current Price

```http
GET /api/prices/current/{product_id}
```

**Response:**

```json
{
  "product_id": "PROD-001",
  "name": "Premium Widget",
  "current_price": 15.99,
  "cost_price": 8.0,
  "margin_pct": 49.8
}
```

#### Apply Recommended Price

```http
POST /api/prices/apply/{product_id}
Content-Type: application/json

{
  "price": 18.50,
  "reason": "agent_recommendation"
}
```

**Response:**

```json
{
  "success": true,
  "product_id": "PROD-001",
  "new_price": 18.5,
  "applied_at": "2024-03-19T10:31:00Z",
  "reason": "agent_recommendation"
}
```

#### Get Price History

```http
GET /api/prices/history/{product_id}?days=30
```

**Response:**

```json
[
  {
    "date": "2024-03-19T10:31:00Z",
    "price": 18.5,
    "reason": "agent_recommendation"
  },
  {
    "date": "2024-03-18T08:00:00Z",
    "price": 15.99,
    "reason": "manual_adjustment"
  }
]
```

---

### **2. INVENTORY** — Stock levels and reorder management

#### List All Inventory

```http
GET /api/inventory/items
```

**Response:**

```json
[
  {
    "product_id": "PROD-001",
    "product_name": "Premium Widget",
    "current_stock": 150,
    "reorder_point": 50,
    "status": "healthy",
    "days_to_stockout": 28.8
  }
]
```

#### Get Inventory for Specific Product

```http
GET /api/inventory/items/{product_id}
```

**Response:**

```json
{
  "product_id": "PROD-001",
  "product_name": "Premium Widget",
  "current_stock": 150,
  "reorder_point": 50,
  "status": "healthy",
  "days_to_stockout": 28.8
}
```

#### Update Stock

```http
PUT /api/inventory/items/{product_id}
Content-Type: application/json

{
  "quantity_change": -10,
  "reason": "manual_adjustment"
}
```

**Response:**

```json
{
  "success": true,
  "product_id": "PROD-001",
  "quantity_change": -10,
  "new_stock": 140,
  "status": "healthy",
  "updated_at": "2024-03-19T10:32:00Z"
}
```

#### Get Reorder Alerts

```http
GET /api/inventory/alerts?urgency=all
```

**Query Parameters:**

- `urgency`: `critical`, `warning`, `info`, or `all` (default)

**Response:**

```json
[
  {
    "product_id": "PROD-005",
    "product_name": "Basic Item",
    "current_stock": 8,
    "reorder_point": 25,
    "days_to_stockout": 1.6,
    "urgency": "critical"
  }
]
```

#### Get Inventory Metrics

```http
GET /api/inventory/metrics
```

**Response:**

```json
{
  "total_items": 12,
  "total_units": 2450,
  "total_value": 34800.0,
  "items_low_stock": 2,
  "items_critical": 0,
  "health_score": 0.87,
  "average_turnover": 4.5
}
```

---

### **3. TRANSACTIONS (POS)** — Record sales and get statistics

#### Record POS Transaction

```http
POST /api/pos/transaction
Content-Type: application/json

{
  "items": [
    {
      "product_id": "PROD-001",
      "quantity": 2,
      "price": 18.50,
      "subtotal": 37.00
    },
    {
      "product_id": "PROD-003",
      "quantity": 1,
      "price": 12.99,
      "subtotal": 12.99
    }
  ],
  "total": 49.99,
  "payment_method": "cash",
  "notes": "Customer #1234"
}
```

**Response:**

```json
{
  "transaction_id": "TXN-2024-001234",
  "items": [...],
  "total": 49.99,
  "timestamp": "2024-03-19T10:33:00Z",
  "status": "completed"
}
```

**What happens:**

- ✓ Inventory is decremented
- ✓ PriceHistory is updated
- ✓ Transaction is recorded in database
- ✓ Agent receives feedback for learning

#### Get Recent Transactions

```http
GET /api/pos/transactions?limit=50&days=30
```

**Response:**

```json
[
  {
    "transaction_id": "TXN-2024-001234",
    "items_count": 2,
    "total": 49.99,
    "timestamp": "2024-03-19T10:33:00Z",
    "payment_method": "cash"
  }
]
```

#### Get POS Statistics

```http
GET /api/pos/stats?days=30
```

**Response:**

```json
{
  "total_transactions": 156,
  "total_revenue": 4521.5,
  "average_transaction_value": 28.99,
  "items_sold": 287,
  "period": "Last 30 days"
}
```

---

### **4. METRICS & DASHBOARD** — System performance and insights

#### Dashboard Summary

```http
GET /api/metrics/dashboard?days=30
```

**Response:**

```json
{
  "total_revenue": 4521.5,
  "revenue_trend": "up",
  "total_transactions": 156,
  "average_order_value": 28.99,
  "inventory_health": 0.87,
  "items_low_stock": 2,
  "items_critical": 0,
  "avg_price_change": 2.3,
  "pricing_confidence": 0.84,
  "last_updated": "2024-03-19T10:33:00Z"
}
```

#### Recommendation Metrics

```http
GET /api/metrics/recommendations?days=30
```

**Response:**

```json
{
  "total_recommendations": 156,
  "recommendations_applied": 142,
  "applied_rate": 91.0,
  "avg_confidence": 0.84,
  "avg_revenue_impact": 0.12
}
```

#### Pricing Opportunities

```http
GET /api/metrics/opportunities?limit=10
```

**Response:**

```json
[
  {
    "product_id": "PROD-001",
    "product_name": "Premium Widget",
    "current_price": 15.99,
    "recommended_price": 18.5,
    "potential_impact": "increase_revenue",
    "expected_change": 15.6,
    "confidence": 0.89
  }
]
```

#### Performance Metrics

```http
GET /api/metrics/performance
```

**Response:**

```json
{
  "uptime_pct": 99.9,
  "avg_recommendation_latency_ms": 150,
  "successful_predictions": 142,
  "failed_predictions": 14,
  "accuracy": 91.0,
  "last_training_date": "2024-03-18T22:00:00Z"
}
```

---

## 🔄 Complete Workflow

### Example: Get Recommendation → Apply → Record Sale

```bash
# 1. Get recommendation for product
curl "http://localhost:8000/api/prices/recommend/PROD-001?agent_type=ppo"

# Response:
# {
#   "recommended_price": 18.50,
#   "confidence": 0.87,
#   "factors": {...}
# }

# 2. Apply the recommendation
curl -X POST "http://localhost:8000/api/prices/apply/PROD-001" \
  -H "Content-Type: application/json" \
  -d '{"price": 18.50, "reason": "agent_recommendation"}'

# 3. Record POS transaction at that price
curl -X POST "http://localhost:8000/api/pos/transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": "PROD-001", "quantity": 1, "price": 18.50, "subtotal": 18.50}],
    "total": 18.50
  }'

# 4. Check updated metrics
curl "http://localhost:8000/api/metrics/dashboard"
```

---

## 📱 Frontend Integration Checklist

- [ ] Call `/api/prices/recommend/{product_id}` to display price suggestions
- [ ] Call `/api/prices/apply/{product_id}` when user approves recommendation
- [ ] Call `/api/pos/transaction` after each sale in POS
- [ ] Call `/api/inventory/items` to display stock levels dashboard
- [ ] Call `/api/inventory/alerts?urgency=critical` to show urgent reorders
- [ ] Call `/api/metrics/dashboard` to populate main dashboard
- [ ] Call `/api/metrics/opportunities` to show optimization suggestions
- [ ] Call `/api/pos/stats` to show sales performance

---

## 🚨 Error Handling

All errors follow standard HTTP status codes:

- `200 OK` — Request succeeded
- `400 Bad Request` — Invalid parameters
- `404 Not Found` — Product/resource not found
- `500 Internal Server Error` — Server error (check logs)

**Error Response:**

```json
{
  "detail": "Product PROD-999 not found"
}
```

---

## 🔐 Security Notes

- CORS enabled for `localhost:5173` (Vite dev server) and `localhost:3000`
- All endpoints accept JSON
- No authentication yet (add in production)
- Sensitive data (prices, costs) should be protected

---

## 📈 Next Steps

1. ✅ **API Endpoints** — Created and documented
2. ⏳ **Frontend Integration** — Connect React to these endpoints
3. ⏳ **Real-time Updates** — Add WebSocket for live pricing
4. ⏳ **Authentication** — Add JWT tokens
5. ⏳ **Rate Limiting** — Prevent abuse
6. ⏳ **Logging** — Track all requests
