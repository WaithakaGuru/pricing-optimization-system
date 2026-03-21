#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test the pricing service fix."""
import sys
from services.pricing_service import PricingService
import sqlite3

# Handle Windows encoding issues
if sys.platform == "win32":
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Check database for sample product
conn = sqlite3.connect('pricing.db')
cur = conn.cursor()
cur.execute('SELECT id, name, current_price FROM products LIMIT 1')
product = cur.fetchone()
print(f'Sample product: {product}')
conn.close()

# Test pricing service
service = PricingService(agent_type='ppo')
if product:
    rec = service.get_recommendation(product[0])
    if rec:
        print(f'[OK] Recommendation generated for {product[1]}')
        print(f'  Current: ${rec["current_price"]:.2f}')
        print(f'  Recommended: ${rec["recommended_price"]:.2f}')
    else:
        print('[FAIL] Could not generate recommendation')
