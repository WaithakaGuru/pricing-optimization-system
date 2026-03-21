"""Test script for StateBuilder."""
from rl.environment.state_builder import StateBuilder
from models import Product, InventoryItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import numpy as np

# Initialize database connection
db_url = "sqlite:///pricing.db"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

# Create a test product
session = Session()

# Check if test product exists, if not create it
test_product = session.query(Product).filter(Product.id == "TEST-001").first()
if not test_product:
    test_product = Product(
        id="TEST-001",
        name="Test Product",
        cost_price=5.0,
        min_price=1.0,
        max_price=50.0,
        current_price=15.0
    )
    session.add(test_product)
    
    # Add inventory
    inventory = InventoryItem(
        product_id="TEST-001",
        quantity=100,
        reorder_point=20,
        reorder_quantity=50
    )
    session.add(inventory)
    session.commit()
    print("✅ Created test product TEST-001")
else:
    print("✅ Test product already exists")

session.close()

# Test StateBuilder
print("\n🧠 Testing StateBuilder...")
state_builder = StateBuilder()
state = state_builder.build_state("TEST-001")

print(f"\n📊 State Vector for TEST-001:")
print(f"Shape: {state.shape}")
print(f"Values: {state}")
print(f"\nFeature Breakdown:")
for i, name in enumerate(state_builder.feature_names):
    print(f"  {name:25s} = {state[i]:.4f}")

print("\n✅ StateBuilder test successful!")
