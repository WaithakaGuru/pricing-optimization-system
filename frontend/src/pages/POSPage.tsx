import { useState, useEffect } from "react";
import type { Product, Transaction } from "../types";
import { useCartStore } from "../store";
import ProductGrid from "../components/pos/ProductGrid";
import CartPanel from "../components/pos/CartPanel";
import { productsApi, posApi } from "../api/client";

export default function POSPage() {
  const { items, addItem, removeItem, updateQty, clearCart, total } =
    useCartStore();
  const [products, setProducts] = useState<Product[]>([]);
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [lastTxnId, setLastTxnId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch products and transactions on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [productsData, transactionsData] = await Promise.all([
          productsApi.list(),
          posApi.transactions(30),
        ]);
        setProducts(productsData);
        setTxns(transactionsData as Transaction[]);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const isToday = (ts: string) =>
    new Date(ts).toDateString() === new Date().toDateString();
  const todayTxns = txns.filter((t) => isToday(t.timestamp));
  const todayRevenue = todayTxns.reduce((s, t) => s + t.total, 0);

  function handleCheckout() {
    if (items.length === 0) return;
    const txn: Transaction = {
      id: `TXN-${Date.now()}`,
      items: items.map((i) => ({
        product_id: i.product_id,
        product_name: i.product_name,
        quantity: i.quantity,
        price: i.price,
      })),
      total: total(),
      timestamp: new Date().toISOString(),
    };
    setTxns((prev) => [txn, ...prev]);
    setLastTxnId(txn.id);
    clearCart();
    setTimeout(() => setLastTxnId(null), 5000);
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-2 max-w-350 bg-white items-center justify-center" style={{ height: "calc(100vh - 60px - 56px)" }}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[--color-accent]"></div>
        <span className="text-[--color-text-tertiary]">Loading products...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-2 max-w-350 bg-white" style={{ height: "calc(100vh - 60px - 56px)", minHeight: "600px" }}>
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <span className="text-red-700 text-sm font-medium">Error: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div
        className="flex flex-col gap-2 max-w-350 bg-white"
        style={{ height: "calc(100vh - 60px - 56px)", minHeight: "600px" }}
      >
        {/* Stats strip */}
        <div className="bg-[--color-surface] border border-[--color-border] rounded-xl flex items-center px-6 pb-2 shadow-xs shrink-0">
          {[
            {
              label: "Today's Revenue",
              value: `$${todayRevenue.toFixed(2)}`,
              mono: true,
              accent: false,
            },
            {
              label: "Transactions Today",
              value: `${todayTxns.length}`,
              mono: true,
              accent: false,
            },
            {
              label: "Items in Cart",
              value: `${items.reduce((s, i) => s + i.quantity, 0)}`,
              mono: true,
              accent: false,
            },
            {
              label: "Cart Total",
              value: `$${total().toFixed(2)}`,
              mono: true,
              accent: true,
            },
          ].map((s, i, arr) => (
            <div key={s.label} className="flex items-center flex-1">
              <div className="flex flex-col gap-0.5 py-3.5 flex-1">
                <span className="text-[10px] font-semibold uppercase tracking-widest text-[--color-text-tertiary]">
                  {s.label}
                </span>
                <span
                  className={`text-lg font-semibold leading-tight font-mono ${s.accent ? "text-[--color-accent]" : "text-[--color-text-primary]"}`}
                >
                  {s.value}
                </span>
              </div>
              {i < arr.length - 1 && (
                <div className="w-px h-9 bg-[--color-border] mx-6 shrink-0" />
              )}
            </div>
          ))}
        </div>

        {/* Main 2-col - grows to fill available space */}
        <div
          className="grid gap-4 flex-1"
          style={{ gridTemplateColumns: "1fr 320px" }}
        >
          <div className="min-h-120 relative overflow-hidden flex flex-col bg-[--color-surface] border border-[--color-border] rounded-2xl shadow-xs p-4">
            <ProductGrid
              products={products}
              onAdd={(p: Product) => addItem(p)}
            />
          </div>
          <div className=" flex flex-col">
            <CartPanel
              items={items}
              total={total()}
              onUpdateQty={updateQty}
              onRemove={removeItem}
              onCheckout={handleCheckout}
              onClear={clearCart}
              lastTxnId={lastTxnId}
            />
          </div>
        </div>

        {/* Transaction log */}
        <div className="bg-[--color-surface] border border-[--color-border] rounded-2xl shadow-xs shrink-0">
          <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-[--color-border] shrink-0">
            <h2 className="text-sm font-semibold text-[--color-text-primary]">
              Transaction Log
            </h2>
            <span className="text-[11px] text-[--color-text-tertiary] bg-[--color-surface-2] px-2 py-0.5 rounded-full">
              {txns.length} total
            </span>
          </div>
          {/* Log head */}
          <div
            className="grid px-5 py-2 bg-[--color-surface-2] border-b border-[--color-border] text-[10px] font-semibold uppercase tracking-widest text-[--color-text-tertiary] shrink-0"
            style={{ gridTemplateColumns: "140px 1fr 90px 70px" }}
          >
            <span>ID</span>
            <span>Items</span>
            <span>Total</span>
            <span>Time</span>
          </div>
          {/* Log body - scrollable */}
          <div className="overflow-y-auto flex-1 h-100">
            {txns.slice(0, 8).map((t, i) => (
              <div
                key={t.id}
                className="grid items-center px-5 py-2.5 border-b border-[--color-border] last:border-0 hover:bg-[--color-surface-2] transition-colors text-xs animate-fade-up"
                style={{
                  gridTemplateColumns: "140px 1fr 90px 70px",
                  animationDelay: `${i * 25}ms`,
                }}
              >
                <span className="font-mono text-[--color-accent]">{t.id}</span>
                <span className="text-[--color-text-secondary] truncate pr-4">
                  {t.items
                    .map((i) => `${i.product_name} ×${i.quantity}`)
                    .join(", ")}
                </span>
                <span className="font-semibold text-[--color-text-primary] font-mono">
                  ${t.total.toFixed(2)}
                </span>
                <span className="text-[--color-text-tertiary]">
                  {new Date(t.timestamp).toLocaleTimeString("en-US", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
