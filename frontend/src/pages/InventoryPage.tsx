import { useState } from "react";
import { useAsync } from "../hooks";
import { inventoryApi } from "../api/client";
import { MOCK_INVENTORY } from "../api/mock";
import type { InventoryItem } from "../types";
import StockBadge, { getStockStatus } from "../components/inventory/StockBadge";
import StockBar from "../components/inventory/StockBar";
import AdjustModal from "../components/inventory/AdjustModal";
import ProductForm from "../components/products/ProductForm";

type Filter = "all" | "critical" | "low" | "ok" | "overstock";

const COL = "2.5fr 1fr 1.8fr 1fr 1fr 1fr 80px";

export default function InventoryPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<InventoryItem | null>(null);
  const [showAddProduct, setShowAddProduct] = useState(false);

  const { data, loading, error, refetch } = useAsync(
    () => inventoryApi.list().catch(() => MOCK_INVENTORY),
    true,
  );

  // Use nullish coalescing to ensure items is always an array
  const items = data ?? MOCK_INVENTORY;

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

  function handleSave() {
    refetch();
    setEditing(null);
  }

  if (error && items.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading inventory data</p>
      </div>
    );
  }

  if (loading && items.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-text-secondary">Loading inventory...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 max-w-300">
      {/* Alert banner */}
      {alerts.length > 0 && (
        <div className="flex items-center gap-2.5 px-4 py-3 bg-warning-light border border-amber-200 rounded-xl text-warning] text-sm animate-fade-up">
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
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search products…"
            className="w-full h-9 pl-8 pr-3 border border-border rounded-md bg-surface text-sm text-text-primary placeholder:text-text-tertiary outline-none focus:border-accent transition-colors"
          />
        </div>
        <button
          onClick={() => setShowAddProduct(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-accent bg-accent-light text-accent text-xs font-medium hover:opacity-90 transition-opacity whitespace-nowrap"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M8 2v12M2 8h12"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          Add Product
        </button>
        <div className="flex gap-1.5 flex-wrap">
          {(["all", "critical", "low", "ok", "overstock"] as Filter[]).map(
            (f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md border text-xs font-medium transition-all ${
                  filter === f
                    ? "bg-accent-light border-accent text-accent"
                    : "bg-surface border-border text-text-secondary hover:border-accent hover:text-accent"
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-full ${filter === f ? "bg-accent/15 text-accent" : "bg-surface-2] text-text-tertiary"}`}
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
        {/* thead */}
        <div
          className="grid px-6 py-2.5 bg-surface-2] border-b border-border text-[10.5px] font-semibold uppercase tracking-widest text-text-tertiary items-center"
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
            return (
              <div
                key={item.id}
                className="grid items-center px-6 py-3.5 border-b border-border last:border-0 hover:bg-surface-2] transition-colors animate-fade-up"
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
          {filtered.length} of {items!.length} products
        </span>
        <span>
          Total units:{" "}
          <strong className="text-text-secondary font-semibold">
            {items!.reduce((s, i) => s + i.quantity, 0).toLocaleString()}
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

      {showAddProduct && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 flex items-center justify-between px-6 py-4 border-b bg-white">
              <h2 className="text-lg font-semibold text-text-primary">
                Add New Product
              </h2>
              <button
                onClick={() => setShowAddProduct(false)}
                className="text-text-tertiary hover:text-text-primary transition-colors"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M18 6L6 18M6 6l12 12"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>
            <div className="p-6">
              <ProductForm
                onSuccess={() => {
                  setShowAddProduct(false);
                  refetch();
                }}
                onCancel={() => setShowAddProduct(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
