import type { POSCartItem } from '../../types';

interface Props {
  items: POSCartItem[];
  total: number;
  onUpdateQty: (productId: string, qty: number) => void;
  onRemove: (productId: string) => void;
  onCheckout: () => void;
  onClear: () => void;
  lastTxnId: string | null;
}

export default function CartPanel({ items, total, onUpdateQty, onRemove, onCheckout, onClear, lastTxnId }: Props) {
  const isEmpty = items.length === 0;
  const tax = total * 0.16;

  return (
    <div className="bg-[--color-surface] border border-[--color-border] rounded-2xl flex flex-col h-full shadow-sm overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[--color-border] flex-shrink-0">
        <h2 className="text-sm font-semibold text-[--color-text-primary]">Current Order</h2>
        {!isEmpty && (
          <button onClick={onClear}
            className="text-xs font-medium text-[--color-danger] bg-[--color-danger-light] border border-red-200 px-2.5 py-1 rounded-md hover:opacity-80 transition-opacity">
            Clear
          </button>
        )}
      </div>

      {/* Success banner */}
      {lastTxnId && (
        <div className="flex items-center gap-2 px-5 py-2.5 bg-[--color-success-light] border-b border-green-200 text-[--color-success] text-xs font-medium animate-fade-up">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" className="flex-shrink-0">
            <circle cx="8" cy="8" r="7" fill="currentColor" opacity=".2"/>
            <path d="M5 8l2.5 2.5L11 5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Sale recorded · <span className="font-mono">{lastTxnId}</span>
        </div>
      )}

      {/* Items */}
      <div className="flex-1 overflow-y-auto">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center gap-3 h-44 text-[--color-text-tertiary]">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <path d="M5 5h5l5 20h16l5-12H10" stroke="var(--color-border-2)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="18" cy="33" r="2" fill="var(--color-border-2)"/>
              <circle cx="30" cy="33" r="2" fill="var(--color-border-2)"/>
            </svg>
            <span className="text-sm">Add products to begin a sale</span>
          </div>
        ) : (
          items.map((item) => (
            <div key={item.product_id}
              className="grid items-center gap-2 px-5 py-2.5 border-b border-[--color-border] last:border-0 hover:bg-[--color-surface-2] transition-colors animate-fade-up"
              style={{ gridTemplateColumns: '1fr auto auto auto' }}>
              <div className="min-w-0">
                <p className="text-xs font-medium text-[--color-text-primary] truncate">{item.product_name}</p>
                <p className="text-[10.5px] text-[--color-text-tertiary] font-mono">${item.price.toFixed(2)} each</p>
              </div>
              <div className="flex items-center gap-1.5">
                <button onClick={() => onUpdateQty(item.product_id, item.quantity - 1)}
                  className="w-6 h-6 rounded bg-[--color-surface-2] border border-[--color-border] text-sm text-[--color-text-primary] flex items-center justify-center hover:bg-[--color-border] transition-colors leading-none">
                  −
                </button>
                <span className="text-xs font-semibold text-[--color-text-primary] font-mono w-4 text-center">{item.quantity}</span>
                <button onClick={() => onUpdateQty(item.product_id, item.quantity + 1)}
                  className="w-6 h-6 rounded bg-[--color-surface-2] border border-[--color-border] text-sm text-[--color-text-primary] flex items-center justify-center hover:bg-[--color-border] transition-colors leading-none">
                  +
                </button>
              </div>
              <span className="text-xs font-semibold text-[--color-text-primary] font-mono w-12 text-right">
                ${(item.price * item.quantity).toFixed(2)}
              </span>
              <button onClick={() => onRemove(item.product_id)}
                className="w-5 h-5 rounded text-[--color-text-tertiary] text-[10px] flex items-center justify-center hover:bg-[--color-danger-light] hover:text-[--color-danger] transition-colors">
                ✕
              </button>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 border-t border-[--color-border] bg-[--color-surface-2] px-5 py-4 flex flex-col gap-2">
        <div className="flex justify-between text-xs text-[--color-text-secondary]">
          <span>Subtotal</span>
          <span className="font-mono">${total.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-xs text-[--color-text-secondary]">
          <span>Tax (16%)</span>
          <span className="font-mono">${tax.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-base font-bold text-[--color-text-primary] pt-1.5 border-t border-[--color-border] mt-0.5">
          <span>Total</span>
          <span className="font-mono">${(total + tax).toFixed(2)}</span>
        </div>

        <div className="grid grid-cols-2 gap-2 mt-1">
          <button onClick={onCheckout} disabled={isEmpty}
            className="flex items-center justify-center gap-1.5 h-11 rounded-lg bg-[--color-text-primary] text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#1e2530] transition-colors">
            <CashIcon /> Cash
          </button>
          <button onClick={onCheckout} disabled={isEmpty}
            className="flex items-center justify-center gap-1.5 h-11 rounded-lg bg-[--color-accent] text-white text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[--color-accent-hover] transition-colors">
            <CardIcon /> Card
          </button>
        </div>
      </div>
    </div>
  );
}

function CashIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="4" width="14" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
      <circle cx="8" cy="8.5" r="2" stroke="currentColor" strokeWidth="1.4"/>
    </svg>
  );
}
function CardIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="3" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M1 7h14" stroke="currentColor" strokeWidth="1.4"/>
      <rect x="3" y="9.5" width="4" height="1.5" rx="0.5" fill="currentColor"/>
    </svg>
  );
}
