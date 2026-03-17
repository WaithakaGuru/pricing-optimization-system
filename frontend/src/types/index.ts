export interface Product {
  id: string;
  name: string;
  cost_price: number;
  min_price: number;
  max_price: number;
  current_price: number;
  created_at: string;
  updated_at: string;
}

export interface PriceRecommendation {
  product_id: string;
  current_price: number;
  recommended_price: number;
  confidence: number;
  factors: Record<string, number | string>;
  timestamp: string;
}

export interface PriceHistory {
  id: number;
  product_id: string;
  old_price: number;
  new_price: number;
  reason: string;
  timestamp: string;
}

export interface InventoryItem {
  id: number;
  product_id: string;
  product_name?: string;
  quantity: number;
  reorder_point: number;
  reorder_quantity: number;
  expiry_date?: string;
  updated_at: string;
}

export type StockStatus = 'ok' | 'low' | 'critical' | 'overstock';

export interface TransactionItem {
  product_id: string;
  product_name?: string;
  quantity: number;
  price: number;
}

export interface Transaction {
  id: string;
  items: TransactionItem[];
  total: number;
  timestamp: string;
}

export interface POSCartItem {
  product_id: string;
  product_name: string;
  quantity: number;
  price: number;
}

export type TimeRange = '7d' | '30d' | '90d';
