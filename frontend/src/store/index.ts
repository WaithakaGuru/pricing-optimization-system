import { create } from 'zustand';
import type { POSCartItem, Product } from '../types';

interface CartStore {
  items: POSCartItem[];
  addItem: (product: Product) => void;
  removeItem: (productId: string) => void;
  updateQty: (productId: string, qty: number) => void;
  clearCart: () => void;
  total: () => number;
}

export const useCartStore = create<CartStore>((set, get) => ({
  items: [],
  addItem: (product) =>
    set((s) => {
      const existing = s.items.find((i) => i.product_id === product.id);
      if (existing) {
        return { items: s.items.map((i) => i.product_id === product.id ? { ...i, quantity: i.quantity + 1 } : i) };
      }
      return { items: [...s.items, { product_id: product.id, product_name: product.name, quantity: 1, price: product.current_price }] };
    }),
  removeItem: (productId) => set((s) => ({ items: s.items.filter((i) => i.product_id !== productId) })),
  updateQty: (productId, qty) =>
    set((s) => ({
      items: qty <= 0
        ? s.items.filter((i) => i.product_id !== productId)
        : s.items.map((i) => i.product_id === productId ? { ...i, quantity: qty } : i),
    })),
  clearCart: () => set({ items: [] }),
  total: () => get().items.reduce((sum, i) => sum + i.price * i.quantity, 0),
}));
