import type {
  Product,
  PriceRecommendation,
  PriceHistory,
  InventoryItem,
  Transaction,
} from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as any).detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const pricesApi = {
  recommend: (productId: string) =>
    req<PriceRecommendation>(`/api/prices/recommend/${productId}`),
  apply: (productId: string, price: number) =>
    req<{ success: boolean }>("/api/prices/apply", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, price }),
    }),
  history: (productId: string, days = 30) =>
    req<PriceHistory[]>(`/api/prices/history/${productId}?days=${days}`),
};

export const inventoryApi = {
  list: () => req<InventoryItem[]>("/api/inventory/items"),
  update: (productId: string, newQuantity: number, oldQuantity: number) =>
    req<InventoryItem>(`/api/inventory/items/${productId}`, {
      method: "PUT",
      body: JSON.stringify({
        quantity_change: newQuantity - oldQuantity,
        reason: "adjustment",
      }),
    }),
  alerts: () => req<InventoryItem[]>("/api/inventory/alerts"),
};

export const posApi = {
  record: (transaction: Omit<Transaction, "id">) =>
    req<{ id: string; success: boolean }>("/api/pos/transaction", {
      method: "POST",
      body: JSON.stringify(transaction),
    }),
  transactions: (limit = 100) =>
    req<Transaction[]>(`/api/pos/transactions?limit=${limit}`),
  stats: () => req<any>("/api/pos/stats"),
};

export const productsApi = {
  list: () => req<Product[]>("/api/products"),
  create: (data: {
    id: string;
    name: string;
    cost_price: number;
    min_price: number;
    max_price: number;
    current_price: number;
    initial_quantity: number;
    reorder_point: number;
    reorder_quantity: number;
    warehouse_location: string;
  }) =>
    req<Product>("/api/products", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export const dashboardApi = {
  summary: (days = 30) => req<any>(`/api/metrics/dashboard?days=${days}`),
};

export const analyticsApi = {
  revenueData: (days = 30) => req<any[]>(`/api/analytics/revenue?days=${days}`),
  categoryData: () => req<any[]>("/api/analytics/categories"),
  recommendations: () => req<any[]>("/api/analytics/recommendations"),
};
