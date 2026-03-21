import { useState } from "react";
import type { InventoryItem } from "../../types";

interface Props {
  item: InventoryItem;
  onClose: () => void;
  onSave: (productId: string, newQty: number, oldQty: number) => void;
}

type Reason = "restock" | "correction" | "damage";

export default function AdjustModal({ item, onClose, onSave }: Props) {
  const [qty, setQty] = useState(item.quantity);
  const [reason, setReason] = useState<Reason>("restock");
  const diff = qty - item.quantity;

  return (
    <div
      className="fixed inset-0 bg-[#0D1117]/45 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-up"
      onClick={onClose}
    >
      <div
        className="bg-surface border border-border rounded-2xl w-110 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-5 border-b border-border">
          <div>
            <h2 className="text-base font-semibold text-text-primary">
              Adjust Stock
            </h2>
            <p className="text-xs text-text-tertiary mt-0.5 max-w-70 truncate">
              {item.product_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-md bg-surface-2] text-text-tertiary text-xs flex items-center justify-center hover:bg-border hover:text-text-primary transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 flex flex-col gap-4">
          {/* Current vs new */}
          <div className="flex items-center gap-3 bg-surface-2] rounded-xl p-4">
            <div className="flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-text-tertiary">
                Current
              </p>
              <p className="text-2xl font-semibold text-text-primary font-mono leading-tight mt-0.5">
                {item.quantity}
              </p>
            </div>
            <span className="text-xl text-border-2]">→</span>
            <div className="flex-1 text-right">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-text-tertiary">
                New
              </p>
              <p
                className={`text-2xl font-semibold font-mono leading-tight mt-0.5 ${diff > 0 ? "text-success]" : diff < 0 ? "text-danger" : "text-text-primary"}`}
              >
                {qty}
              </p>
            </div>
            {diff !== 0 && (
              <span
                className={`text-xs font-semibold font-mono px-2 py-1 rounded-md ml-1 ${diff > 0 ? "bg-success-light text-success]" : "bg-danger-light text-danger"}`}
              >
                {diff > 0 ? "+" : ""}
                {diff}
              </span>
            )}
          </div>

          {/* Qty stepper */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-widest text-text-secondary block mb-2">
              New Quantity
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setQty((q) => Math.max(0, q - 1))}
                className="w-9 h-9 rounded-md bg-surface-2] border border-border text-lg text-text-primary flex items-center justify-center hover:bg-border transition-color shrink-0"
              >
                −
              </button>
              <input
                type="number"
                min={0}
                value={qty}
                onChange={(e) =>
                  setQty(Math.max(0, parseInt(e.target.value) || 0))
                }
                className="flex-1 h-9 border border-border rounded-md text-center text-base font-semibold text-text-primary font-mono bg-surface] outline-none focus:border-accent transition-colors [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
              />
              <button
                onClick={() => setQty((q) => q + 1)}
                className="w-9 h-9 rounded-md bg-surface-2] border border-border text-lg text-text-primary flex items-center justify-center hover:bg-border transition-colors shrink-0"
              >
                +
              </button>
            </div>
          </div>

          {/* Reason */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-widest text-text-secondary block mb-2">
              Reason
            </label>
            <div className="flex gap-2">
              {(["restock", "correction", "damage"] as Reason[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setReason(r)}
                  className={`flex-1 py-2 rounded-md text-xs font-medium border transition-all ${
                    reason === r
                      ? "bg-accent-light border-accent text-accent"
                      : "bg-surface] border-border text-text-secondary hover:border-accent hover:text-accent"
                  }`}
                >
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2.5 px-6 py-4 border-t border-border">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-md border border-border text-sm font-medium text-text-secondary bg-surface] hover:bg-surface-2] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onSave(item.product_id, qty, item.quantity);
              onClose();
            }}
            className="px-5 py-2 rounded-md bg-accent text-sm font-medium text-white hover:bg-accent-hover transition-colors"
          >
            Save Adjustment
          </button>
        </div>
      </div>
    </div>
  );
}
