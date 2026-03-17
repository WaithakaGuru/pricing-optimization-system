import type { Product, InventoryItem, Transaction } from '../types';

export const MOCK_PRODUCTS: Product[] = [
  { id: 'p001', name: 'Arabica Coffee Beans 1kg',    cost_price: 8.50,  min_price: 12, max_price: 28, current_price: 18.99, created_at: '2025-01-01', updated_at: '2025-03-10' },
  { id: 'p002', name: 'Organic Green Tea 200g',      cost_price: 4.20,  min_price: 7,  max_price: 18, current_price: 11.50, created_at: '2025-01-01', updated_at: '2025-03-12' },
  { id: 'p003', name: 'Cold Brew Concentrate 500ml', cost_price: 5.80,  min_price: 9,  max_price: 20, current_price: 14.99, created_at: '2025-01-01', updated_at: '2025-03-15' },
  { id: 'p004', name: 'Matcha Powder Premium 100g',  cost_price: 11.00, min_price: 18, max_price: 40, current_price: 24.99, created_at: '2025-01-01', updated_at: '2025-03-08' },
  { id: 'p005', name: 'Herbal Chamomile Mix 50g',    cost_price: 2.10,  min_price: 4,  max_price: 12, current_price: 7.49,  created_at: '2025-01-01', updated_at: '2025-03-14' },
  { id: 'p006', name: 'Espresso Roast Dark 500g',    cost_price: 7.20,  min_price: 11, max_price: 24, current_price: 16.99, created_at: '2025-01-01', updated_at: '2025-03-11' },
];

export const MOCK_INVENTORY: InventoryItem[] = [
  { id: 1, product_id: 'p001', product_name: 'Arabica Coffee Beans 1kg',    quantity: 142, reorder_point: 50, reorder_quantity: 200, updated_at: '2025-03-16' },
  { id: 2, product_id: 'p002', product_name: 'Organic Green Tea 200g',      quantity: 28,  reorder_point: 40, reorder_quantity: 150, updated_at: '2025-03-16' },
  { id: 3, product_id: 'p003', product_name: 'Cold Brew Concentrate 500ml', quantity: 11,  reorder_point: 30, reorder_quantity: 100, updated_at: '2025-03-15' },
  { id: 4, product_id: 'p004', product_name: 'Matcha Powder Premium 100g',  quantity: 85,  reorder_point: 20, reorder_quantity: 80,  updated_at: '2025-03-16' },
  { id: 5, product_id: 'p005', product_name: 'Herbal Chamomile Mix 50g',    quantity: 6,   reorder_point: 25, reorder_quantity: 120, updated_at: '2025-03-14' },
  { id: 6, product_id: 'p006', product_name: 'Espresso Roast Dark 500g',    quantity: 210, reorder_point: 60, reorder_quantity: 150, updated_at: '2025-03-16' },
];

export const MOCK_TRANSACTIONS: Transaction[] = Array.from({ length: 18 }, (_, i) => ({
  id: `TXN-${1000 + i}`,
  items: [{ product_id: MOCK_PRODUCTS[i % 6].id, product_name: MOCK_PRODUCTS[i % 6].name, quantity: (i % 3) + 1, price: MOCK_PRODUCTS[i % 6].current_price }],
  total: +((MOCK_PRODUCTS[i % 6].current_price * ((i % 3) + 1))).toFixed(2),
  timestamp: new Date(Date.now() - i * 1000 * 60 * 23).toISOString(),
}));

export function generateRevenueData(days = 30) {
  const data = [];
  let base = 1200;
  for (let i = days; i >= 0; i--) {
    const date = new Date(Date.now() - i * 86_400_000);
    base += (Math.random() - 0.44) * 180;
    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      revenue: Math.max(600, Math.round(base)),
      transactions: Math.floor(Math.random() * 40 + 20),
    });
  }
  return data;
}

export function generateCategoryData() {
  return [
    { name: 'Coffee',    value: 42, color: '#1A56FF' },
    { name: 'Tea',       value: 28, color: '#12A169' },
    { name: 'Cold Brew', value: 18, color: '#D97706' },
    { name: 'Other',     value: 12, color: '#CDD2DB' },
  ];
}
