import { useState, useEffect } from "react";
import { inventoryApi } from "../api/client";
import { ErrorNotice, LoadingSkeleton } from "../components/common/LoadingUI";
import type { InventoryItem } from "../types";
import StockBadge, { getStockStatus } from "../components/inventory/StockBadge";
import StockBar from "../components/inventory/StockBar";
import AdjustModal from "../components/inventory/AdjustModal";

type Filter = "all" | "critical" | "low" | "ok" | "overstock";

const COL = "2.5fr 1fr 1.8fr 1fr 1fr 1fr 80px";

export default function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<InventoryItem | null>(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  // Handle responsive layout
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    async function loadItems() {
      try {
        setLoading(true);
        const data = await inventoryApi.list();
        setItems(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load inventory",
        );
      } finally {
        setLoading(false);
      }
    }
    loadItems();
  }, []);

  const alerts = items.filter((i) => {
    const s = getStockStatus(i.quantity, i.reorder_point);
    return s === "critical" || s === "low";
  });

  const filtered = items.filter((i) => {
    const s = getStockStatus(i.quantity, i.reorder_point);
    return (
      (filter === "all" || s === filter) &&
      (i.product_name ?? "").toLowerCase().includes(search.toLowerCase())
    );
  });
  const counts = (
    ["all", "critical", "low", "ok", "overstock"] as Filter[]
  ).reduce(
    (acc, f) => {
      acc[f] =
        f === "all"
          ? items.length
          : items.filter(
              (i) => getStockStatus(i.quantity, i.reorder_point) === f,
            ).length;
      return acc;
    },
    {} as Record<Filter, number>,
  );

  async function handleSave(productId: string, newQty: number) {
    try {
      const updated = await inventoryApi.update(productId, newQty);
      setItems((prev) =>
        prev.map((i) => (i.product_id === productId ? updated : i)),
      );
      setEditing(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update inventory",
      );
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-5">
        <LoadingSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Error notice */}
      {error && (
        <ErrorNotice message={error} onRetry={() => window.location.reload()} />
      )}

      {/* Alert banner */}
      {alerts.length > 0 && (
        <div className="flex items-center gap-2.5 px-4 py-3 bg-warning-light border border-amber-200 rounded-xl text-warning text-sm animate-fade-up">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            className="shrink-0"
          >
            <path
              d="M8 2L1 14h14L8 2z"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinejoin="round"
            />
            <path
              d="M8 7v3M8 12v.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <span className="flex-1">
            <strong className="font-semibold">
              {alerts.length} item{alerts.length > 1 ? "s" : ""}
            </strong>{" "}
            need attention — {alerts.map((a) => a.product_name).join(", ")}
          </span>
          <button
            onClick={() => setFilter("critical")}
            className="text-xs font-medium border border-current px-2.5 py-1 rounded-md hover:bg-amber-100 transition-colors whitespace-nowrap"
          >
            Show critical
          </button>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-50 max-w-xs">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary"
            width="13"
            height="13"
            viewBox="0 0 16 16"
            fill="none"
          >
            <circle
              cx="7"
              cy="7"
              r="5"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <path
              d="M11 11l3 3"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search products…"
            className="w-full h-9 pl-8 pr-3 border border-border rounded-md bg-surface text-sm text-text-primary placeholder:text-text-tertiary outline-none focus:border-accent transition-colors"
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {(["all", "critical", "low", "ok", "overstock"] as Filter[]).map(
            (f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-xs font-medium transition-all ${
                  filter === f
                    ? "bg-accent-light] border-accent] text-accent"
                    : "bg-surface border-border text-text-secondary hover:border-accent hover:text-accent"
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-full ${filter === f ? "bg-accent/15 text-accent" : "bg-surface-2 text-text-tertiary"}`}
                >
                  {counts[f]}
                </span>
              </button>
            ),
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-surface border border-border rounded-2xl shadow-xs overflow-hidden">
        {/* Desktop table header */}
        <div
          className="hidden md:grid px-6 py-3 border-b border-border text-xs font-semibold uppercase tracking-widest text-text-tertiary gap-4"
          style={{ gridTemplateColumns: COL }}
        >
          <span>Product</span>
          <span>Status</span>
          <span>Stock Level</span>
          <span>Reorder Pt.</span>
          <span>Reorder Qty</span>
          <span>Updated</span>
          <span></span>
        </div>

        {filtered.length === 0 ? (
          <p className="text-center text-sm text-text-tertiary py-10">
            No items match your filter.
          </p>
        ) : (
          filtered.map((item, i) => {
            const status = getStockStatus(item.quantity, item.reorder_point);
            const updated = new Date(item.updated_at).toLocaleDateString(
              "en-US",
              { month: "short", day: "numeric" },
            );

            // Mobile card layout
            if (isMobile) {
              return (
                <div
                  key={item.id}
                  className="border-b border-border last:border-0 px-4 py-4 space-y-3 hover:bg-surface-2 transition-colors animate-fade-up"
                  style={{ animationDelay: `${i * 30}ms` }}
                >
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-text-primary truncate">
                        {item.product_name}
                      </p>
                      <p className="text-[10px] text-text-tertiary font-mono">
                        {item.product_id}
                      </p>
                    </div>
                    <StockBadge status={status} />
                  </div>
                  <StockBar qty={item.quantity} reorder={item.reorder_point} />
                  <div className="flex justify-between text-xs">
                    <div>
                      <span className="text-text-tertiary">Reorder: </span>
                      <span className="text-text-secondary font-mono">
                        {item.reorder_point}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-tertiary">Qty: </span>
                      <span className="text-text-secondary font-mono">
                        {item.reorder_quantity}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-border">
                    <span className="text-xs text-text-tertiary">
                      {updated || item.updated_at}
                    </span>
                    <button
                      onClick={() => setEditing(item)}
                      className="text-xs font-medium px-3 py-1.5 rounded-md border border-border text-text-secondary bg-surface hover:border-accent hover:text-accent hover:bg-accent-light transition-all"
                    >
                      Adjust
                    </button>
                  </div>
                </div>
              );
            }

            // Desktop table layout
            return (
              <div
                key={item.id}
                className="grid items-center px-6 py-3.5 border-b border-border last:border-0 hover:bg-surface-2 transition-colors animate-fade-up"
                style={{
                  gridTemplateColumns: COL,
                  animationDelay: `${i * 30}ms`,
                }}
              >
                <div className="min-w-0 pr-4">
                  <p className="text-sm font-medium text-text-primary truncate">
                    {item.product_name}
                  </p>
                  <p className="text-[10.5px] text-text-tertiary font-mono">
                    {item.product_id}
                  </p>
                </div>
                <StockBadge status={status} />
                <StockBar qty={item.quantity} reorder={item.reorder_point} />
                <span className="text-sm text-text-secondary font-mono">
                  {item.reorder_point}
                </span>
                <span className="text-sm text-text-secondary font-mono">
                  {item.reorder_quantity}
                </span>
                <span className="text-xs text-text-tertiary">{updated}</span>
                <button
                  onClick={() => setEditing(item)}
                  className="text-xs font-medium px-3 py-1.5 rounded-md border border-border text-text-secondary bg-surface hover:border-accent hover:text-accent hover:bg-accent-light transition-all"
                >
                  Adjust
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div className="flex justify-between text-xs text-text-tertiary px-1">
        <span>
          {filtered.length} of {items.length} products
        </span>
        <span>
          Total units:{" "}
          <strong className="text-text-secondary font-semibold">
            {items.length > 0
              ? items
                  .reduce((s, i) => s + (i.quantity || 0), 0)
                  .toLocaleString()
              : "0"}
          </strong>
        </span>
      </div>

      {editing && (
        <AdjustModal
          item={editing}
          onClose={() => setEditing(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
