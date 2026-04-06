"""Check product price bounds in database."""
import sqlite3

conn = sqlite3.connect("pricing.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 100)
print("PRODUCT PRICE BOUNDS")
print("=" * 100)

cursor.execute("""
    SELECT id, name, cost_price, current_price, min_price, max_price
    FROM products
    ORDER BY id
""")

products = cursor.fetchall()

print(f"\n{'ID':<15} {'Name':<30} {'Cost':<8} {'Current':<8} {'Min':<8} {'Max':<8}")
print("-" * 100)

for p in products:
    print(f"{p['id']:<15} {p['name']:<30} ${p['cost_price']:<7.2f} ${p['current_price']:<7.2f} ${p['min_price']:<7.2f} ${p['max_price']:<7.2f}")

print("\n" + "=" * 100)

conn.close()
