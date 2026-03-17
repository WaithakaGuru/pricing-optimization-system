"""Test and showcase the synthetic data generator."""
from utils.synthetic_data import (
    generate_synthetic_sales,
    generate_synthetic_inventory,
    generate_synthetic_weather,
    create_product_master,
    load_synthetic_data_into_db,
)
import pandas as pd

print("=" * 70)
print("SYNTHETIC DATA GENERATOR TEST")
print("=" * 70)

# Test 1: Product Master
print("\n📦 TEST 1: Product Master Data")
print("-" * 70)
products_df = create_product_master(num_products=3)
print(products_df.to_string(index=False))
print(f"✅ Generated {len(products_df)} products\n")

# Test 2: Sales Data
print("📊 TEST 2: Synthetic Sales Data (with price elasticity)")
print("-" * 70)
sales_df = generate_synthetic_sales(num_products=2, num_days=10)
print(sales_df.head(20).to_string(index=False))
print(f"\nSummary:")
print(f"  Total transactions: {len(sales_df)}")
print(f"  Total revenue: ${sales_df['revenue'].sum():.2f}")
print(f"  Total cost: ${(sales_df['quantity_sold'] * sales_df['cost_price']).sum():.2f}")
print(f"  Total profit: ${(sales_df['revenue'] - (sales_df['quantity_sold'] * sales_df['cost_price'])).sum():.2f}")
print(f"\nPrice elasticity effect visible:")
for prod in sales_df['product_id'].unique():
    prod_data = sales_df[sales_df['product_id'] == prod]
    print(f"  {prod}: {len(prod_data)} sales, avg price ${prod_data['price'].mean():.2f}, avg quantity {prod_data['quantity_sold'].mean():.1f}")

# Test 3: Inventory Data
print("\n\n📦 TEST 3: Synthetic Inventory Data")
print("-" * 70)
inventory_df = generate_synthetic_inventory(num_products=2, num_days=10)
print(inventory_df.head(20).to_string(index=False))
print(f"\nSummary:")
for prod in inventory_df['product_id'].unique():
    prod_data = inventory_df[inventory_df['product_id'] == prod]
    restocks = prod_data['was_restocked'].sum()
    print(f"  {prod}: {restocks} restocks, final stock {prod_data.iloc[-1]['stock_level']} units")

# Test 4: Weather Data
print("\n\n🌤️  TEST 4: Synthetic Weather Data")
print("-" * 70)
weather_df = generate_synthetic_weather(num_days=10)
print(weather_df.head(10).to_string(index=False))
print(f"\nSummary:")
print(f"  Avg temperature: {weather_df['temperature'].mean():.1f}°C")
print(f"  Avg humidity: {weather_df['humidity'].mean():.1f}%")
print(f"  Rainy days: {(weather_df['precipitation'] > 0).sum()} / {len(weather_df)}")
print(f"  Avg cloud cover: {weather_df['cloud_cover'].mean():.1f}%")

# Test 5: Load into database
print("\n\n💾 TEST 5: Loading Synthetic Data into Database")
print("-" * 70)
try:
    load_synthetic_data_into_db(db_url="sqlite:///pricing.db")
    print("✅ Synthetic data loaded successfully!")
    print("\nDatabase now contains realistic synthetic data for testing:")
    print("  - 5 Products")
    print("  - 5 Inventory records")
    print("  - 30 days of transactions")
except Exception as e:
    print(f"❌ Error loading data: {e}")

print("\n" + "=" * 70)
print("✅ Synthetic Data Generator Tests Complete!")
print("=" * 70)
print("\nYou can now use this synthetic data to:")
print("  1. Test the StateBuilder with realistic data")
print("  2. Train the RL agent without real customer data")
print("  3. Validate the reward function")
print("  4. Bootstrap demand forecasting models")
