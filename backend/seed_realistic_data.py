"""
Seed realistic product data with 100+ products and 90 days of sales history.
Run with: python seed_realistic_data.py
"""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Base, Product, InventoryItem, Transaction, PriceHistory, engine, SessionLocal
import logging
import uuid
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PRODUCT DEFINITIONS
# ============================================================================

PRODUCTS_DATA = {
    "Beverages": [
        {"name": "Arabica Coffee Beans 1kg", "cost": 8.50, "base_price": 18.99, "elasticity": 0.8},
        {"name": "Robusta Coffee Beans 1kg", "cost": 6.50, "base_price": 14.99, "elasticity": 0.85},
        {"name": "Ethiopian Yirgacheffe 500g", "cost": 7.20, "base_price": 16.99, "elasticity": 0.75},
        {"name": "Colombian Geisha 500g", "cost": 12.00, "base_price": 28.99, "elasticity": 0.6},
        {"name": "Brazilian Santos 1kg", "cost": 7.80, "base_price": 17.49, "elasticity": 0.82},
        {"name": "Vietnamese Robusta 1kg", "cost": 5.50, "base_price": 12.49, "elasticity": 0.9},
        {"name": "Organic Green Tea 200g", "cost": 4.20, "base_price": 11.50, "elasticity": 0.7},
        {"name": "Matcha Powder Premium 100g", "cost": 11.00, "base_price": 24.99, "elasticity": 0.65},
        {"name": "Herbal Chamomile Mix 50g", "cost": 2.10, "base_price": 7.49, "elasticity": 0.75},
        {"name": "Peppermint Tea 100g", "cost": 2.80, "base_price": 8.99, "elasticity": 0.78},
        {"name": "Cold Brew Concentrate 500ml", "cost": 5.80, "base_price": 14.99, "elasticity": 0.72},
        {"name": "Espresso Roast Dark 500g", "cost": 7.20, "base_price": 16.99, "elasticity": 0.8},
        {"name": "Light Roast Blonde 500g", "cost": 6.80, "base_price": 15.99, "elasticity": 0.82},
        {"name": "Irish Breakfast Tea 50 Bags", "cost": 3.50, "base_price": 9.99, "elasticity": 0.8},
        {"name": "Oolong Dragon Well 200g", "cost": 8.50, "base_price": 19.99, "elasticity": 0.7},
        {"name": "Jasmine Pearls Tea 150g", "cost": 6.20, "base_price": 15.49, "elasticity": 0.72},
        {"name": "Blue Butterfly Pea Flower 50g", "cost": 4.80, "base_price": 12.99, "elasticity": 0.65},
        {"name": "Rooibos Red Bush Tea 100g", "cost": 3.20, "base_price": 8.99, "elasticity": 0.78},
        {"name": "White Peony Tea 100g", "cost": 5.50, "base_price": 13.99, "elasticity": 0.7},
        {"name": "Black Pu-erh Tea 100g", "cost": 7.00, "base_price": 16.99, "elasticity": 0.68},
        {"name": "Turmeric Latte Mix 200g", "cost": 4.50, "base_price": 11.99, "elasticity": 0.75},
        {"name": "Chai Spice Mix 100g", "cost": 3.80, "base_price": 10.49, "elasticity": 0.78},
        {"name": "Butterfly Pea Latte Mix 150g", "cost": 5.20, "base_price": 13.99, "elasticity": 0.72},
        {"name": "Honey Golden Blend 500g", "cost": 6.50, "base_price": 15.99, "elasticity": 0.73},
        {"name": "Medium Roast Balance 500g", "cost": 7.00, "base_price": 16.49, "elasticity": 0.81},
        {"name": "Kenya AA Grade 500g", "cost": 8.80, "base_price": 20.99, "elasticity": 0.75},
        {"name": "Costa Rica Tarrazú 500g", "cost": 9.20, "base_price": 21.99, "elasticity": 0.73},
        {"name": "Guatemala Antigua 500g", "cost": 8.50, "base_price": 19.99, "elasticity": 0.76},
        {"name": "Peru Organic 500g", "cost": 7.80, "base_price": 18.49, "elasticity": 0.78},
        {"name": "Decaf Swiss Water 500g", "cost": 9.50, "base_price": 22.99, "elasticity": 0.68},
    ],
    "Snacks": [
        {"name": "Almond & Honey Granola 400g", "cost": 3.50, "base_price": 9.99, "elasticity": 0.85},
        {"name": "Raw Almonds 500g", "cost": 6.80, "base_price": 14.99, "elasticity": 0.8},
        {"name": "Cashew Clusters 300g", "cost": 5.50, "base_price": 12.99, "elasticity": 0.78},
        {"name": "Walnut & Date Mix 200g", "cost": 4.20, "base_price": 10.49, "elasticity": 0.82},
        {"name": "Pistachio Roasted 250g", "cost": 6.50, "base_price": 14.99, "elasticity": 0.75},
        {"name": "Energy Protein Bar (Box of 12)", "cost": 4.80, "base_price": 11.99, "elasticity": 0.88},
        {"name": "Dark Chocolate Granola 350g", "cost": 3.80, "base_price": 10.49, "elasticity": 0.84},
        {"name": "Coconut Hemp Bites 200g", "cost": 3.20, "base_price": 8.99, "elasticity": 0.86},
        {"name": "Organic Chia Seed Pudding Mix 150g", "cost": 2.50, "base_price": 7.49, "elasticity": 0.8},
        {"name": "Fruit & Nut Mix 300g", "cost": 3.90, "base_price": 9.99, "elasticity": 0.83},
        {"name": "Sesame Snap Bars (Box of 10)", "cost": 2.80, "base_price": 7.99, "elasticity": 0.87},
        {"name": "Pumpkin Seed Trail Mix 250g", "cost": 3.60, "base_price": 9.49, "elasticity": 0.84},
        {"name": "Keto Chocolate Bites 150g", "cost": 3.40, "base_price": 9.99, "elasticity": 0.82},
        {"name": "Quinoa Pops 200g", "cost": 3.10, "base_price": 8.49, "elasticity": 0.85},
        {"name": "Roasted Chickpea Snack 200g", "cost": 2.20, "base_price": 6.49, "elasticity": 0.88},
        {"name": "Freeze Dried Berries 100g", "cost": 4.50, "base_price": 11.99, "elasticity": 0.78},
        {"name": "Salted Seaweed Crisps 50g", "cost": 1.80, "base_price": 5.99, "elasticity": 0.82},
        {"name": "Mulberry & Almond Bars 200g", "cost": 3.50, "base_price": 9.99, "elasticity": 0.84},
        {"name": "Matcha Energy Bites 150g", "cost": 3.80, "base_price": 10.99, "elasticity": 0.8},
        {"name": "Raw Cacao Nibs 200g", "cost": 2.90, "base_price": 8.49, "elasticity": 0.81},
        {"name": "Goji Berry Blend 150g", "cost": 4.20, "base_price": 10.99, "elasticity": 0.77},
        {"name": "Bee Pollen 100g", "cost": 3.50, "base_price": 10.49, "elasticity": 0.75},
        {"name": "Mixed Dried Fruit 300g", "cost": 2.80, "base_price": 7.99, "elasticity": 0.84},
        {"name": "Hazelnut & Chocolate Granola 400g", "cost": 3.70, "base_price": 10.49, "elasticity": 0.83},
        {"name": "Sunflower Seed Butter 350g", "cost": 3.20, "base_price": 9.49, "elasticity": 0.83},
    ],
    "Health & Wellness": [
        {"name": "Protein Powder Vanilla 1kg", "cost": 8.50, "base_price": 21.99, "elasticity": 0.72},
        {"name": "Collagen Peptides 300g", "cost": 6.80, "base_price": 17.99, "elasticity": 0.7},
        {"name": "Spirulina Powder 100g", "cost": 4.50, "base_price": 12.99, "elasticity": 0.75},
        {"name": "Ashwagandha Root Powder 100g", "cost": 3.20, "base_price": 9.49, "elasticity": 0.78},
        {"name": "Greens Superfood Mix 300g", "cost": 8.00, "base_price": 19.99, "elasticity": 0.68},
        {"name": "Omega-3 Fish Oil Capsules 120", "cost": 7.50, "base_price": 18.99, "elasticity": 0.7},
        {"name": "Vitamin D3 Softgels 1000IU", "cost": 3.80, "base_price": 10.99, "elasticity": 0.75},
        {"name": "Probiotics Multi-strain 90 caps", "cost": 6.50, "base_price": 15.99, "elasticity": 0.72},
        {"name": "Magnesium Glycinate 300g", "cost": 4.20, "base_price": 11.99, "elasticity": 0.76},
        {"name": "B-Complex Energy Blend 100g", "cost": 3.50, "base_price": 10.49, "elasticity": 0.77},
        {"name": "Whey Protein Chocolate 1kg", "cost": 8.20, "base_price": 20.99, "elasticity": 0.73},
        {"name": "Vegan Protein Blend 800g", "cost": 7.80, "base_price": 19.49, "elasticity": 0.71},
        {"name": "MCT Oil 500ml", "cost": 5.50, "base_price": 13.99, "elasticity": 0.74},
        {"name": "Turmeric Curcumin Extract 60 caps", "cost": 4.80, "base_price": 12.49, "elasticity": 0.75},
        {"name": "Vitamin C Powder 200g", "cost": 2.50, "base_price": 7.99, "elasticity": 0.8},
        {"name": "Zinc Lozenges 30 tablets", "cost": 1.80, "base_price": 5.99, "elasticity": 0.82},
        {"name": "Biotin Hair Growth 120 caps", "cost": 3.20, "base_price": 9.99, "elasticity": 0.76},
        {"name": "Joint Support Formula 90 caps", "cost": 5.50, "base_price": 14.99, "elasticity": 0.73},
        {"name": "Adaptogens Blend 100g", "cost": 4.80, "base_price": 13.49, "elasticity": 0.75},
        {"name": "Immune Boost Tea Blend 100g", "cost": 3.50, "base_price": 10.49, "elasticity": 0.78},
    ],
    "Kitchen Equipment": [
        {"name": "Digital Coffee Scale 0-5kg", "cost": 12.50, "base_price": 29.99, "elasticity": 0.5},
        {"name": "Pour Over Dripper Ceramic", "cost": 3.80, "base_price": 10.99, "elasticity": 0.65},
        {"name": "French Press 34oz", "cost": 6.50, "base_price": 15.99, "elasticity": 0.6},
        {"name": "Burr Grinder Adjustable", "cost": 18.00, "base_price": 42.99, "elasticity": 0.45},
        {"name": "Gooseneck Kettle 1.2L", "cost": 8.50, "base_price": 21.99, "elasticity": 0.55},
        {"name": "Bamboo Tea Infuser Balls Set", "cost": 2.20, "base_price": 6.99, "elasticity": 0.72},
        {"name": "Stainless Tumbler 16oz", "cost": 4.50, "base_price": 11.99, "elasticity": 0.68},
        {"name": "Bamboo Coffee Scoops Set", "cost": 1.50, "base_price": 4.99, "elasticity": 0.75},
        {"name": "Glass Measuring Cup 250ml", "cost": 2.80, "base_price": 7.99, "elasticity": 0.7},
        {"name": "Milk Frother Electric", "cost": 7.20, "base_price": 17.99, "elasticity": 0.58},
        {"name": "Reusable Coffee Filters", "cost": 1.80, "base_price": 5.99, "elasticity": 0.78},
        {"name": "Tea Kettle Stovetop 1.5L", "cost": 5.50, "base_price": 14.99, "elasticity": 0.62},
        {"name": "Cabinet Tea Organizer", "cost": 8.00, "base_price": 19.99, "elasticity": 0.55},
        {"name": "Thermos Flask 500ml", "cost": 6.80, "base_price": 16.99, "elasticity": 0.6},
        {"name": "Coffee Mat Non-slip", "cost": 2.50, "base_price": 7.49, "elasticity": 0.72},
    ],
    "Baked Goods": [
        {"name": "Sourdough Starter Kit", "cost": 4.50, "base_price": 11.99, "elasticity": 0.68},
        {"name": "Almond Flour 1kg", "cost": 5.80, "base_price": 14.99, "elasticity": 0.72},
        {"name": "Coconut Flour 500g", "cost": 3.20, "base_price": 8.99, "elasticity": 0.75},
        {"name": "Tapioca Starch 500g", "cost": 2.50, "base_price": 6.99, "elasticity": 0.8},
        {"name": "Psyllium Husk 200g", "cost": 2.80, "base_price": 7.99, "elasticity": 0.78},
        {"name": "Xanthan Gum 100g", "cost": 3.50, "base_price": 9.99, "elasticity": 0.73},
        {"name": "Yeast Active Dry 11oz", "cost": 4.80, "base_price": 12.99, "elasticity": 0.68},
        {"name": "Monk Fruit Sweetener 200g", "cost": 5.20, "base_price": 13.99, "elasticity": 0.65},
        {"name": "Erythritol Sweetener 500g", "cost": 2.50, "base_price": 7.99, "elasticity": 0.78},
        {"name": "Vanilla Extract Pure 4oz", "cost": 6.50, "base_price": 15.99, "elasticity": 0.6},
    ],
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_product_id(counter: int) -> str:
    """Generate product ID like p001, p002, etc."""
    return f"p{counter:04d}"


def generate_realistic_sales_data(
    product_id: str,
    base_price: float,
    elasticity: float,
    num_days: int = 90
) -> tuple[list[dict], list[dict]]:
    """
    Generate realistic transaction and price history data.
    
    Returns: (transactions, price_changes)
    """
    transactions = []
    price_changes = []
    
    current_date = datetime.now() - timedelta(days=num_days)
    current_price = base_price
    
    # Generate 40-200 transactions over the period (realistic sales volume)
    num_transactions = random.randint(40, 200)
    transaction_dates = [current_date + timedelta(days=random.random() * num_days) for _ in range(num_transactions)]
    transaction_dates.sort()
    
    # Generate 2-5 price changes during the period
    num_price_changes = random.randint(2, 5)
    price_change_days = sorted(random.sample(range(1, num_days), num_price_changes))
    price_change_idx = 0
    
    for i, tx_date in enumerate(transaction_dates):
        days_elapsed = (tx_date - current_date).days
        
        # Check if price should change at this point
        while price_change_idx < len(price_change_days) and days_elapsed >= price_change_days[price_change_idx]:
            old_price = current_price
            # Random price adjustment constrained by min/max prices (±15% of base)
            min_p = base_price * 0.85
            max_p = base_price * 1.15
            current_price = random.uniform(min_p, max_p)
            
            price_changes.append({
                "product_id": product_id,
                "old_price": old_price,
                "new_price": current_price,
                "reason": random.choice(["rl_recommendation", "seasonal_adjustment", "competitor_match", "demand_response"]),
                "timestamp": tx_date,
            })
            price_change_idx += 1
        
        # Quantity: influenced by price elasticity (lower price = higher quantity)
        price_factor = (current_price - base_price) / base_price if base_price > 0 else 0
        elasticity_effect = 1 - (elasticity * price_factor)  # Negative price change increases quantity
        base_quantity = random.randint(1, 10)
        quantity = max(1, int(base_quantity * elasticity_effect * random.uniform(0.7, 1.3)))
        
        revenue = current_price * quantity
        
        transactions.append({
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "quantity": quantity,
            "price": round(current_price, 2),
            "revenue": round(revenue, 2),
            "total": round(revenue, 2),
            "payment_method": random.choice(["cash", "card", "mobile", "check"]),
            "notes": random.choice([None, "Bulk order", "Promotional", "Regular", "VIP customer"]),
            "timestamp": tx_date,
        })
    
    return transactions, price_changes


def seed_products(session: Session):
    """Seed 100+ products with realistic data."""
    logger.info("Starting data seed...")
    
    # Clear existing data
    session.query(Transaction).delete()
    session.query(PriceHistory).delete()
    session.query(InventoryItem).delete()
    session.query(Product).delete()
    session.commit()
    logger.info("✅ Cleared existing data")
    
    product_counter = 1
    total_transactions = 0
    total_price_changes = 0
    
    # Create products and related data for each category
    for category, products_list in PRODUCTS_DATA.items():
        logger.info(f"\n📦 Seeding {category}...")
        
        for product_def in products_list:
            product_id = generate_product_id(product_counter)
            
            # Create product
            product = Product(
                id=product_id,
                name=product_def["name"],
                cost_price=product_def["cost"],
                min_price=product_def["cost"] * 1.2,  # Min 20% markup
                max_price=product_def["cost"] * 3.5,  # Max 350% markup
                current_price=product_def["base_price"],
                created_at=datetime.utcnow() - timedelta(days=120),
                updated_at=datetime.utcnow(),
            )
            session.add(product)
            session.flush()  # Ensure product is created before referencing
            
            # Create inventory
            base_quantity = random.randint(20, 200)
            inventory = InventoryItem(
                product_id=product_id,
                quantity=base_quantity,
                reorder_point=base_quantity // 3,
                reorder_quantity=base_quantity // 2,
                warehouse_location=random.choice(["Main Warehouse", "Back Storage", "Display", "Cold Storage", "Transit"]),
                last_restock_date=datetime.utcnow() - timedelta(days=random.randint(5, 30)),
            )
            session.add(inventory)
            
            # Generate transaction and price history
            transactions, price_changes = generate_realistic_sales_data(
                product_id,
                product_def["base_price"],
                product_def["elasticity"],
                num_days=90
            )
            
            # Add transactions
            for tx_data in transactions:
                tx = Transaction(**tx_data)
                session.add(tx)
            total_transactions += len(transactions)
            
            # Add price changes
            for pc_data in price_changes:
                pc = PriceHistory(**pc_data)
                session.add(pc)
            total_price_changes += len(price_changes)
            
            product_counter += 1
            
            # Log progress every 10 products
            if product_counter % 10 == 0:
                logger.info(f"  ✅ Processed {product_counter} products...")
        
        logger.info(f"  ✅ {category}: {len(products_list)} products seeded")
    
    # Commit all changes
    session.commit()
    
    total_products = product_counter - 1
    logger.info(f"\n" + "=" * 60)
    logger.info(f"✅ DATA SEEDING COMPLETED")
    logger.info(f"=" * 60)
    logger.info(f"Products:       {total_products}")
    logger.info(f"Transactions:   {total_transactions}")
    logger.info(f"Price Changes:  {total_price_changes}")
    logger.info(f"Categories:     {len(PRODUCTS_DATA)}")
    logger.info(f"Date Range:     Last 90 days")
    logger.info(f"=" * 60)


if __name__ == "__main__":
    # Create tables
    Base.metadata.create_all(engine)
    
    # Seed data
    session = SessionLocal()
    try:
        seed_products(session)
        logger.info("\n✨ Ready for training and dashboard visualization!")
    except Exception as e:
        logger.error(f"❌ Error seeding data: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()
