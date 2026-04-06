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
  const [checkingOut, setCheckingOut] = useState(false);

  // Fetch products and transactions on mount + auto-refresh
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [productsData, transactionsData] = await Promise.all([
          productsApi.list(),
          posApi.transactions(100), // Fetch more recent transactions
        ]);
        setProducts(productsData);
        // Sort by timestamp descending (newest first)
        const sorted = (transactionsData as Transaction[]).sort(
          (a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
        );
        setTxns(sorted);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // No auto-refresh - only refresh on new transactions
    return () => {};
  }, []);

  // Track cart changes and send to backend
  // useEffect(() => {
  //   const updateCartOnBackend = async () => {
  //     if (items.length === 0) return;

  //     try {
  //       await posApi.updateCart(
  //         items.map((item) => ({
  //           product_id: item.product_id,
  //           quantity: item.quantity,
  //           price: item.price,
  //         }))
  //       );
  //     } catch (err) {
  //       console.warn("Failed to sync cart to backend:", err);
  //       // Don't block UI if sync fails, but log it
  //     }
  //   };

  //   // Debounce cart updates - only sync after 500ms of no changes
  //   const timer = setTimeout(updateCartOnBackend, 500);
  //   return () => clearTimeout(timer);
  // }, [items]);

  const isToday = (ts: string) =>
    new Date(ts).toDateString() === new Date().toDateString();
  const todayTxns = txns.filter((t) => isToday(t.timestamp));
  const todayRevenue = todayTxns.reduce((s, t) => s + t.total, 0);

  // Group transactions by date
  const groupedTxns = txns.reduce(
    (acc, t) => {
      const date = new Date(t.timestamp).toDateString();
      if (!acc[date]) {
        acc[date] = [];
      }
      acc[date].push(t);
      return acc;
    },
    {} as Record<string, typeof txns>,
  );

  // Sort date keys with today first
  const sortedDates = Object.keys(groupedTxns).sort((a, b) => {
    const aIsToday = new Date(a).toDateString() === new Date().toDateString();
    const bIsToday = new Date(b).toDateString() === new Date().toDateString();
    if (aIsToday) return -1;
    if (bIsToday) return 1;
    return new Date(b).getTime() - new Date(a).getTime();
  });

  async function handleCheckout() {
    if (items.length === 0) return;

    try {
      // Build transaction in the format the API expects
      const transaction = {
        items: items.map((i) => ({
          product_id: i.product_id,
          product_name: i.product_name,
          quantity: i.quantity,
          price: i.price,
        })),
        total: total(),
        timestamp: new Date().toISOString(),
        payment_method: "cash" as const,
        notes: "",
      };

      // Record transaction to database
      setCheckingOut(true);
      const result = await posApi.record(transaction);
      setLastTxnId(result.id);
      clearCart();
      setCheckingOut(false);

      // Refresh transaction list immediately after recording (event-driven, not polling)
      const transactionsData = await posApi.transactions(100);
      const sorted = (transactionsData as Transaction[]).sort(
        (a, b) =>
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
      );
      setTxns(sorted);
    } catch (err) {
      console.error("Error recording transaction:", err);
      setError(
        err instanceof Error ? err.message : "Failed to record transaction",
      );
    }
  }

  if (loading) {
    return (
      <div
        className="flex flex-col gap-2 max-w-350 bg-white items-center justify-center"
        style={{ height: "calc(100vh - 60px - 56px)" }}
      >
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
        <span className="text-text-tertiary">Loading products...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex flex-col gap-2 max-w-350 bg-white"
        style={{ height: "calc(100vh - 60px - 56px)", minHeight: "600px" }}
      >
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <span className="text-red-700 text-sm font-medium">
            Error: {error}
          </span>
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
        <div className="bg-surface] border border-border rounded-xl flex items-center px-6 pb-2 shadow-xs shrink-0">
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
                <span className="text-[10px] font-semibold uppercase tracking-widest text-text-tertiary">
                  {s.label}
                </span>
                <span
                  className={`text-lg font-semibold leading-tight font-mono ${s.accent ? "text-accent" : "text-text-primary"}`}
                >
                  {s.value}
                </span>
              </div>
              {i < arr.length - 1 && (
                <div className="w-px h-9 bg-border mx-6 shrink-0" />
              )}
            </div>
          ))}
        </div>

        {/* Main 2-col - grows to fill available space */}
        <div className="grid grid-cols-1 md:grid-cols-[1fr_320px] gap-4 flex-1">
          <div className="max-h-180 relative overflow-y-auto flex flex-col bg-surface] border border-border rounded-2xl shadow-xs p-4">
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
              checkingOut={checkingOut}
            />
          </div>
        </div>

        {/* Transaction log */}
        <div className="bg-surface] border border-border rounded-2xl shadow-xs shrink-0">
          <div className="flex items-center gap-2.5 px-5 py-3.5 border-b border-border shrink-0">
            <h2 className="text-sm font-semibold text-text-primary">
              Transaction Log
            </h2>
            <span className="text-[11px] text-text-tertiary bg-surface-2] px-2 py-0.5 rounded-full">
              {txns.length} total
            </span>
          </div>
          {/* Log head */}
          <div
            className="grid px-5 py-2 bg-surface-2] border-b border-border text-[10px] font-semibold uppercase tracking-widest text-text-tertiary shrink-0"
            style={{ gridTemplateColumns: "25rem 1fr 10rem 9rem" }}
          >
            <span>ID</span>
            <span>Items</span>
            <span>Total</span>
            <span>Time</span>
          </div>
          {/* Log body - scrollable */}
          <div className="overflow-y-auto flex-1 h-100">
            {txns.length === 0 ? (
              <div className="px-5 py-8 text-center text-text-tertiary">
                <p className="text-sm">No transactions yet</p>
              </div>
            ) : (
              sortedDates.map((dateStr, dateIdx) => {
                const dateObj = new Date(dateStr);
                const isCurrentDay = dateStr === new Date().toDateString();
                const dateLabel = isCurrentDay ? (
                  <div className="bg-bg p-3 min-w-40">"Today"</div>
                ) : (
                  <div className="bg-bg p-3 min-w-40">
                    {dateObj.toLocaleDateString("en-US", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </div>
                );

                return (
                  <div key={dateStr}>
                    {/* Date marker */}
                    <div className="sticky top-0 bg-surface-2 border-t border-b border-border px-5 py-2 z-10">
                      <span className="text-[10px] font-semibold uppercase tracking-widest text-text-tertiary">
                        {dateLabel}
                      </span>
                    </div>
                    {/* Transactions for this date */}
                    {groupedTxns[dateStr].map((t, txnIdx) => (
                      <div
                        key={t.id}
                        className="grid items-center px-5 py-2.5 border-b border-border last:border-0 hover:bg-surface-2] transition-colors text-xs animate-fade-up"
                        style={{
                          gridTemplateColumns: "25rem 1fr 10rem 9rem",
                          animationDelay: `${dateIdx * 50 + txnIdx * 25}ms`,
                        }}
                      >
                        <span className="font-mono text-accent">{t.id}</span>
                        <span className="text-text-secondary truncate pr-4">
                          {t.items
                            .map((i) => `${i.product_name} ×${i.quantity}`)
                            .join(", ")}
                        </span>
                        <span className="font-semibold text-text-primary font-mono">
                          ${t.total.toFixed(2)}
                        </span>
                        <span className="text-text-tertiary">
                          {new Date(t.timestamp).toLocaleTimeString("en-US", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    ))}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </>
  );
}
