#!/usr/bin/env python
"""Test transaction recording."""
import requests

data = {
    'items': [
        {
            'product_id': 'p001',
            'product_name': 'Arabica Coffee',
            'quantity': 2,
            'price': 18.99,
            'subtotal': 37.98
        }
    ],
    'total': 37.98,
    'payment_method': 'cash'
}

try:
    response = requests.post('http://localhost:8000/api/pos/transaction', json=data, timeout=5)
    if response.status_code == 200:
        print('[OK] Transaction recorded successfully')
        result = response.json()
        print(f'  Transaction ID: {result["transaction_id"]}')
        print(f'  Total: ${result["total"]:.2f}')
    else:
        print(f'[FAIL] Status {response.status_code}: {response.text}')
except Exception as e:
    print(f'[ERROR] {e}')
