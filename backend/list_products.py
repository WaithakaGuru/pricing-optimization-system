"""List available products in database."""
from models import get_session, Product

session = get_session()
products = session.query(Product).all()

print(f"Total products: {len(products)}\n")
for p in products:
    print(f"  {p.id}: {p.name}")
    print(f"     Price: ${p.prices:.2f}, Min: ${p.min_price:.2f}, Max: ${p.max_price:.2f}")

session.close()
