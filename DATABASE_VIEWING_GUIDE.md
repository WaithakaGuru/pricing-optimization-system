# Database Viewing Guide for Optima

This guide shows you **4 different ways** to view and query data in your SQLite database.

---

## 📊 Quick Summary

| Tool               | Ease        | Power           | Setup             |
| ------------------ | ----------- | --------------- | ----------------- |
| **SQLite Browser** | ⭐⭐⭐ Easy | ⭐⭐ Basic      | Download app      |
| **Prisma Studio**  | ⭐⭐⭐ Easy | ⭐⭐ Basic      | 1 command         |
| **Python/Pandas**  | ⭐⭐⭐ Easy | ⭐⭐⭐ Advanced | Already installed |
| **CLI (sqlite3)**  | ⭐ Hard     | ⭐⭐⭐ Powerful | Built-in          |

---

## Method 1: Prisma Studio (Easiest) ⭐⭐⭐

### Setup

**Note**: Prisma requires `schema.prisma` file. If you're using SQLAlchemy, skip to Method 2 or 3.

If you want to add Prisma:

```bash
npm install -D prisma
npx prisma init
# Then configure schema.prisma for your database
```

### Usage

```bash
cd backend
npx prisma studio
```

This opens a **visual web UI** at `http://localhost:5555` where you can:

- Browse all tables
- Create/edit/delete records
- Filter and search
- Export data

---

## Method 2: SQLite Browser (Recommended for GUI) ⭐⭐⭐

### Installation

**Windows**:

```powershell
# Option A: Download from browser
# https://sqlitebrowser.org/dl/
# → Download "DB Browser for SQLite" → Run installer

# Option B: Use Chocolatey
choco install sqlitebrowser
```

**macOS**:

```bash
brew install db-browser-for-sqlite
```

**Linux (Ubuntu)**:

```bash
sudo apt-get install sqlitebrowser
```

### Usage

1. Launch **DB Browser for SQLite**
2. Click **File → Open** → Navigate to:
   ```
   C:\Users\ADMIN\Desktop\Optima\backend\pricing.db
   ```
3. You'll see all tables on the left:
   - `products` - Product definitions
   - `inventory_items` - Stock levels
   - `transactions` - Sales records
   - `price_history` - Price changes
   - `agent_metrics` - RL agent performance

### Viewing Data

| Action            | Steps                                       |
| ----------------- | ------------------------------------------- |
| **Browse table**  | Click table name → Click "Browse Data" tab  |
| **Execute SQL**   | Click "Execute SQL" tab → Write query → Run |
| **Export to CSV** | Right-click table → Export → CSV            |
| **Add record**    | Browse Data → Click "New Record"            |
| **Edit record**   | Double-click cell                           |

---

## Method 3: Python/Pandas (Most Powerful) ⭐⭐⭐

This is already installed and works from terminal/notebook.

### Quick View - All Tables

Create file `backend/view_db.py`:

```python
"""Quick database viewer using pandas."""
import pandas as pd
from sqlalchemy import create_engine

# Connect to database
engine = create_engine("sqlite:///pricing.db")

# View all tables
print("Tables in database:")
print(engine.table_names())

# View each table
for table in engine.table_names():
    print(f"\n{'='*60}")
    print(f"Table: {table}")
    print(f"{'='*60}")
    df = pd.read_sql_table(table, engine)
    print(df)
    print(f"Rows: {len(df)}")
```

**Run it**:

```bash
cd backend
python view_db.py
```

### Specific Queries

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///pricing.db")

# View products
print("PRODUCTS:")
df_products = pd.read_sql("SELECT * FROM products", engine)
print(df_products)

# View inventory
print("\nINVENTORY:")
df_inv = pd.read_sql("SELECT * FROM inventory_items", engine)
print(df_inv)

# View recent transactions
print("\nRECENT TRANSACTIONS:")
df_trans = pd.read_sql("""
    SELECT product_id, quantity, price, revenue, transaction_date
    FROM transactions
    ORDER BY transaction_date DESC
    LIMIT 20
""", engine)
print(df_trans)

# View price history
print("\nPRICE HISTORY:")
df_prices = pd.read_sql("""
    SELECT product_id, old_price, new_price, changed_by, change_date
    FROM price_history
    ORDER BY change_date DESC
    LIMIT 10
""", engine)
print(df_prices)
```

---

## Method 4: SQLite CLI (Most Powerful for Advanced) ⭐⭐

### Installation

**Windows (PowerShell)**:

```powershell
# Windows 10/11 has sqlite3 built-in, or:
choco install sqlite
```

**macOS/Linux**:

```bash
# Usually already installed
sqlite3 --version
```

### Usage

```bash
cd backend
sqlite3 pricing.db
```

This opens SQLite CLI. Then run queries:

```sql
-- List all tables
.tables

-- Schema for a table
.schema products

-- View products
SELECT * FROM products;

-- View products with columns nicely formatted
.mode column
.headers on
SELECT * FROM products;

-- View inventory with joins
SELECT p.product_id, p.name, i.quantity, i.reorder_point
FROM products p
JOIN inventory_items i ON p.product_id = i.product_id;

-- Count transactions
SELECT COUNT(*) as total_transactions FROM transactions;

-- Sales by product (last 7 days)
SELECT product_id, SUM(quantity) as units_sold, SUM(revenue) as total_revenue
FROM transactions
WHERE transaction_date > datetime('now', '-7 days')
GROUP BY product_id
ORDER BY total_revenue DESC;

-- Price changes this month
SELECT * FROM price_history
WHERE change_date > datetime('now', '-1 month')
ORDER BY change_date DESC;

-- Exit
.quit
```

---

## Method 5: Advanced Python Analysis

Create `backend/analyze_db.py`:

```python
"""Advanced database analysis."""
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

engine = create_engine("sqlite:///pricing.db")

# === PRODUCTS ===
print("=" * 60)
print("PRODUCT ANALYSIS")
print("=" * 60)

products = pd.read_sql("SELECT * FROM products", engine)
print(f"\nTotal products: {len(products)}")
print(f"Price range: ${products['base_price'].min():.2f} - ${products['base_price'].max():.2f}")
print(f"Average price: ${products['base_price'].mean():.2f}")

# === INVENTORY ===
print("\n" + "=" * 60)
print("INVENTORY ANALYSIS")
print("=" * 60)

inventory = pd.read_sql("SELECT * FROM inventory_items", engine)
print(f"\nTotal items: {len(inventory)}")
print(f"Total units in stock: {inventory['quantity'].sum():,}")
print(f"Average stock per product: {inventory['quantity'].mean():.0f}")

low_stock = inventory[inventory['quantity'] < inventory['reorder_point']]
print(f"Items below reorder point: {len(low_stock)}")
if len(low_stock) > 0:
    print("\nLow stock items:")
    print(low_stock[['product_id', 'quantity', 'reorder_point']])

# === TRANSACTIONS ===
print("\n" + "=" * 60)
print("SALES ANALYSIS")
print("=" * 60)

transactions = pd.read_sql("SELECT * FROM transactions", engine)
print(f"\nTotal transactions: {len(transactions)}")
print(f"Total units sold: {transactions['quantity'].sum():,}")
print(f"Total revenue: ${transactions['revenue'].sum():,.2f}")
print(f"Average transaction: ${transactions['revenue'].mean():.2f}")

# Last 7 days
week_ago = (datetime.now() - timedelta(days=7)).isoformat()
recent = transactions[transactions['transaction_date'] > week_ago]
print(f"\nLast 7days: {len(recent)} transactions, ${recent['revenue'].sum():,.2f} revenue")

# Top products
print("\nTop 5 products by revenue:")
top = transactions.groupby('product_id')['revenue'].sum().nlargest(5)
print(top)

# === PRICING ===
print("\n" + "=" * 60)
print("PRICING ANALYSIS")
print("=" * 60)

price_changes = pd.read_sql("SELECT * FROM price_history", engine)
print(f"\nTotal price changes: {len(price_changes)}")
print(f"Changed by agent: {len(price_changes[price_changes['changed_by'] == 'agent'])}")
print(f"Changed by manager: {len(price_changes[price_changes['changed_by'] == 'manager'])}")

# Recent changes
print("\nRecent price changes (last 5):")
recent_prices = price_changes.nlargest(5, 'change_date')[['product_id', 'old_price', 'new_price', 'changed_by', 'change_date']]
print(recent_prices)
```

**Run it**:

```bash
python analyze_db.py
```

---

## Recommended Workflow

### For Development (Visual)

1. **Use Prisma Studio** if available (easiest)
2. **Fall back to SQLite Browser** (no code needed)

### For Analysis

1. **Use Python + Pandas** (powerful + already installed)
2. Create scripts in `backend/` that you reuse

### For Production Debugging

1. **Use SQLite CLI** (fastest for precise queries)
2. Write the query → get answer in seconds

---

## Common Queries You'll Want

### Check Agent Metrics

```sql
SELECT * FROM agent_metrics
ORDER BY episode DESC
LIMIT 10;
```

### See Sales Velocity (last 30 days per product)

```sql
SELECT
    product_id,
    COUNT(*) as sales_count,
    SUM(quantity) as units_sold,
    SUM(revenue) as total_revenue,
    AVG(price) as avg_price
FROM transactions
WHERE transaction_date > datetime('now', '-30 days')
GROUP BY product_id
ORDER BY total_revenue DESC;
```

### Inventory Health Report

```sql
SELECT
    p.product_id,
    p.name,
    i.quantity,
    i.reorder_point,
    CASE
        WHEN i.quantity < i.reorder_point * 0.5 THEN 'CRITICAL'
        WHEN i.quantity < i.reorder_point THEN 'LOW'
        ELSE 'HEALTHY'
    END as status
FROM inventory_items i
JOIN products p ON i.product_id = p.product_id
ORDER BY i.quantity ASC;
```

### Price Optimization Performance

```sql
SELECT
    ph.product_id,
    COUNT(*) as price_changes,
    MAX(ph.new_price) as max_price,
    MIN(ph.new_price) as min_price,
    AVG(ph.new_price) as avg_price
FROM price_history ph
GROUP BY ph.product_id
ORDER BY price_changes DESC;
```

---

## Troubleshooting

**Database file not found**

- Path should be: `C:\Users\ADMIN\Desktop\Optima\backend\pricing.db`
- Make sure you're running from `backend/` directory

**"Table doesn't exist"**

- Run the initialization script first: `python init_db.py`
- Check that all tables are created

**SQLite in use / locked"**

- Make sure no other process has the database open
- Close SQLite Browser or Python session

---

## Next Steps

After viewing the data, you can:

1. **Verify test data** is being created correctly
2. **Monitor agent training** (watch agent_metrics grow)
3. **Track pricing** changes (see price_history)
4. **Analyze sales** patterns (transactions table)

Ready to start using the services with real data?
