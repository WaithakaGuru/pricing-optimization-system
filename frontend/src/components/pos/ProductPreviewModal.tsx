import { useState } from "react";
import type { Product } from "../../types";

interface Props {
  product: Product | null;
  onClose: () => void;
  onAddToCart: (product: Product) => void;
}

function getEmoji(name: string) {
  if (/coffee|espresso/i.test(name)) return "☕";
  if (/matcha/i.test(name)) return "🍃";
  if (/tea/i.test(name)) return "🍵";
  if (/cold|brew/i.test(name)) return "🧊";
  return "📦";
}

export default function ProductPreviewModal({
  product,
  onClose,
  onAddToCart,
}: Props) {
  const [quantity, setQuantity] = useState(1);

  if (!product) return null;

  const handleAddToCart = () => {
    // Add to cart multiple times based on quantity
    for (let i = 0; i < quantity; i++) {
      onAddToCart(product);
    }
    onClose();
    setQuantity(1);
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-up">
      <div className="bg-[--color-surface] border border-[--color-border] rounded-2xl shadow-2xl max-w-sm w-full animate-scale-up">
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-5 border-b border-[--color-border]">
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-[--color-text-primary]">
              {product.name}
            </h2>
            <p className="text-sm text-[--color-text-tertiary] mt-1">
              Product Details
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-[--color-text-tertiary] hover:text-[--color-text-primary] transition-colors p-1 -mt-1 -mr-1"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          {/* Emoji/Visual */}
          <div className="text-6xl text-center mb-6 leading-none">
            {getEmoji(product.name)}
          </div>

          {/* Product Info */}
          <div className="space-y-4 mb-6">
            <div className="flex justify-between items-center p-3 bg-[--color-surface-2] rounded-lg">
              <span className="text-sm text-[--color-text-secondary]">
                Current Price
              </span>
              <span className="text-lg font-semibold text-[--color-accent] font-mono">
                ${product.current_price.toFixed(2)}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 bg-[--color-surface-2] rounded-lg">
              <span className="text-sm text-[--color-text-secondary]">
                Cost Price
              </span>
              <span className="text-lg font-semibold text-[--color-text-primary] font-mono">
                ${product.cost_price.toFixed(2)}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 bg-[--color-surface-2] rounded-lg">
              <span className="text-sm text-[--color-text-secondary]">
                Margin
              </span>
              <span className="text-lg font-semibold text-green-600 font-mono">
                {(
                  ((product.current_price - product.cost_price) /
                    product.cost_price) *
                  100
                ).toFixed(1)}
                %
              </span>
            </div>
          </div>

          {/* Quantity Selector */}
          <div className="mb-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-[--color-text-tertiary] mb-2">
              Quantity
            </p>
            <div className="flex items-center gap-3 bg-[--color-surface-2] p-2 rounded-lg">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-9 h-9 rounded bg-[--color-surface] border border-[--color-border] text-sm text-[--color-text-primary] flex items-center justify-center hover:bg-[--color-border] transition-colors leading-none font-bold"
              >
                −
              </button>
              <input
                type="number"
                min="1"
                value={quantity}
                onChange={(e) =>
                  setQuantity(Math.max(1, parseInt(e.target.value) || 1))
                }
                className="flex-1 h-9 text-center bg-[--color-surface] border border-[--color-border] rounded text-sm font-semibold text-[--color-text-primary] outline-none focus:border-[--color-accent] transition-colors"
              />
              <button
                onClick={() => setQuantity(quantity + 1)}
                className="w-9 h-9 rounded bg-[--color-surface] border border-[--color-border] text-sm text-[--color-text-primary] flex items-center justify-center hover:bg-[--color-border] transition-colors leading-none font-bold"
              >
                +
              </button>
            </div>
          </div>

          {/* Total */}
          <div className="mb-6 p-3 bg-[--color-accent-light] border border-[--color-accent]/20 rounded-lg">
            <p className="text-xs text-[--color-text-tertiary] mb-1">
              Total for this order
            </p>
            <p className="text-xl font-bold text-[--color-accent] font-mono">
              ${(product.current_price * quantity).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Footer / Actions */}
        <div className="flex gap-2 px-6 py-4 border-t border-[--color-border] bg-[--color-surface-2]">
          <button
            onClick={onClose}
            className="flex-1 h-10 rounded-lg border border-[--color-border] bg-[--color-surface] text-sm font-semibold text-[--color-text-primary] hover:bg-[--color-border] transition-colors"
          >
            Close
          </button>
          <button
            onClick={handleAddToCart}
            className="flex-1 h-10 rounded-lg bg-[--color-accent] text-white text-sm font-semibold hover:bg-[--color-accent-hover] transition-colors flex items-center justify-center gap-2"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a1 1 0 0 1 1 1v5h5a1 1 0 1 1 0 2h-5v5a1 1 0 1 1-2 0v-5H2a1 1 0 0 1 0-2h5V3a1 1 0 0 1 1-1z" />
            </svg>
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
}
