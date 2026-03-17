import { useState } from 'react';
import type { InventoryItem } from '../../types';

interface Props {
  item: InventoryItem;
  onClose: () => void;
  onSave: (productId: string, newQty: number) => void;
}

type Reason = 'restock' | 'correction' | 'damage';

export default function AdjustModal({ item, onClose, onSave }: Props) {
  const [qty, setQty] = useState(item.quantity);
  const [reason, setReason] = useState<Reason>('restock');
  const diff = qty - item.quantity;

  return (
    <div className="fixed inset-0 bg-[#0D1117]/45 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-up"
      onClick={onClose}>
      <div className="bg-[--color-surface] border border-[--color-border] rounded-2xl w-[440px] shadow-2xl"
        onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-start justify-between px-6 py-5 border-b border-[--color-border]">
          <div>
            <h2 className="text-base font-semibold text-[--color-text-primary]">Adjust Stock</h2>
            <p className="text-xs text-[--color-text-tertiary] mt-0.5 max-w-[280px] truncate">{item.product_name}</p>
          </div>
          <button onClick={onClose} className="w-7 h-7 rounded-md bg-[--color-surface-2] text-[--color-text-tertiary] text-xs flex items-center justify-center hover:bg-[--color-border] hover:text-[--color-text-primary] transition-colors">
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 flex flex-col gap-4">
          {/* Current vs new */}
          <div className="flex items-center gap-3 bg-[--color-surface-2] rounded-xl p-4">
            <div className="flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[--color-text-tertiary]">Current</p>
              <p className="text-2xl font-semibold text-[--color-text-primary] font-mono leading-tight mt-0.5">{item.quantity}</p>
            </div>
            <span className="text-xl text-[--color-border-2]">→</span>
            <div className="flex-1 text-right">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[--color-text-tertiary]">New</p>
              <p className={`text-2xl font-semibold font-mono leading-tight mt-0.5 ${diff > 0 ? 'text-[--color-success]' : diff < 0 ? 'text-[--color-danger]' : 'text-[--color-text-primary]'}`}>
                {qty}
              </p>
            </div>
            {diff !== 0 && (
              <span className={`text-xs font-semibold font-mono px-2 py-1 rounded-md ml-1 ${diff > 0 ? 'bg-[--color-success-light] text-[--color-success]' : 'bg-[--color-danger-light] text-[--color-danger]'}`}>
                {diff > 0 ? '+' : ''}{diff}
              </span>
            )}
          </div>

          {/* Qty stepper */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-widest text-[--color-text-secondary] block mb-2">New Quantity</label>
            <div className="flex items-center gap-2">
              <button onClick={() => setQty(q => Math.max(0, q - 1))}
                className="w-9 h-9 rounded-md bg-[--color-surface-2] border border-[--color-border] text-lg text-[--color-text-primary] flex items-center justify-center hover:bg-[--color-border] transition-colors flex-shrink-0">
                −
              </button>
              <input type="number" min={0} value={qty}
                onChange={(e) => setQty(Math.max(0, parseInt(e.target.value) || 0))}
                className="flex-1 h-9 border border-[--color-border] rounded-md text-center text-base font-semibold text-[--color-text-primary] font-mono bg-[--color-surface] outline-none focus:border-[--color-accent] transition-colors [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
              />
              <button onClick={() => setQty(q => q + 1)}
                className="w-9 h-9 rounded-md bg-[--color-surface-2] border border-[--color-border] text-lg text-[--color-text-primary] flex items-center justify-center hover:bg-[--color-border] transition-colors flex-shrink-0">
                +
              </button>
            </div>
          </div>

          {/* Reason */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-widest text-[--color-text-secondary] block mb-2">Reason</label>
            <div className="flex gap-2">
              {(['restock', 'correction', 'damage'] as Reason[]).map((r) => (
                <button key={r} onClick={() => setReason(r)}
                  className={`flex-1 py-2 rounded-md text-xs font-medium border transition-all ${
                    reason === r
                      ? 'bg-[--color-accent-light] border-[--color-accent] text-[--color-accent]'
                      : 'bg-[--color-surface] border-[--color-border] text-[--color-text-secondary] hover:border-[--color-accent] hover:text-[--color-accent]'
                  }`}>
                  {r.charAt(0).toUpperCase() + r.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2.5 px-6 py-4 border-t border-[--color-border]">
          <button onClick={onClose}
            className="px-4 py-2 rounded-md border border-[--color-border] text-sm font-medium text-[--color-text-secondary] bg-[--color-surface] hover:bg-[--color-surface-2] transition-colors">
            Cancel
          </button>
          <button onClick={() => { onSave(item.product_id, qty); onClose(); }}
            className="px-5 py-2 rounded-md bg-[--color-accent] text-sm font-medium text-white hover:bg-[--color-accent-hover] transition-colors">
            Save Adjustment
          </button>
        </div>
      </div>
    </div>
  );
}
