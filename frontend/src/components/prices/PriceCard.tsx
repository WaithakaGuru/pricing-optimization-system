import type { Product, PriceRecommendation } from "../../types";

interface PriceCardProps {
  product: Product;
  recommendation?: PriceRecommendation;
  onApply: (productId: string, newPrice: number) => void;
}

export default function PriceCard({
  product,
  recommendation,
  onApply,
}: PriceCardProps) {
  if (!recommendation) {
    return (
      <div className="bg-surface border border-border rounded-xl p-5">
        <div className="h-4 bg-surface-2 rounded w-3/4 mb-3 animate-pulse" />
        <div className="h-10 bg-surface-2 rounded w-1/2 animate-pulse" />
        <div className="mt-4 space-y-2">
          <div className="h-3 bg-surface-2 rounded w-2/3 animate-pulse" />
          <div className="h-3 bg-surface-2 rounded w-1/2 animate-pulse" />
        </div>
      </div>
    );
  }

  const diff = recommendation.recommended_price - product.current_price;
  const pctChange = (diff / product.current_price) * 100;
  const margin =
    ((product.current_price - product.cost_price) / product.current_price) *
    100;
  const newMargin =
    ((recommendation.recommended_price - product.cost_price) /
      recommendation.recommended_price) *
    100;

  if (!product) {
    return (
      <div className="bg-surface border border-border rounded-xl p-5">
        <div className="h-4 bg-surface-2 rounded w-3/4 mb-3 animate-pulse" />
        <div className="h-10 bg-surface-2 rounded w-1/2 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-5 hover:border-accent transition-colors animate-fade-up">
      {/* Product name */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-text-primary truncate leading-tight mb-1">
          {product.name || "Unknown Product"}
        </h3>
        <p className="text-[11px] text-text-tertiary">
          ${(product.cost_price || 0).toFixed(2)} cost
        </p>
      </div>

      {/* Current price */}
      <div className="mb-4">
        <span className="text-[10.5px] font-semibold uppercase tracking-widest text-text-tertiary">
          Current
        </span>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-text-primary font-mono">
            ${(product.current_price || 0).toFixed(2)}
          </span>
          <span className="text-[11px] text-text-tertiary">
            {isNaN(margin) ? 0 : margin.toFixed(1)}% margin
          </span>
        </div>
      </div>

      {/* Recommended price */}
      <div className="mb-5 p-3 bg-accent-light border border-accent rounded-lg">
        <span className="text-[10.5px] font-semibold uppercase tracking-widest text-accent block mb-1">
          Recommended
        </span>
        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-2xl font-bold text-accent font-mono">
            ${(recommendation?.recommended_price || 0).toFixed(2)}
          </span>
          <span
            className={`text-xs font-bold font-mono ${isNaN(pctChange) || diff >= 0 ? "text-success" : "text-danger"}`}
          >
            {diff >= 0 ? "+" : ""}
            {isNaN(pctChange) ? "0.0" : pctChange.toFixed(1)}%
          </span>
        </div>
        <span className="text-[11px] text-accent">
          {isNaN(newMargin) ? 0 : newMargin.toFixed(1)}% margin
        </span>
      </div>

      {/* Factors */}
      <div className="mb-4 p-3 bg-surface-2 rounded-lg">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-text-tertiary block mb-2">
          Factors
        </span>
        <div className="space-y-1">
          {Object.entries(recommendation.factors)
            .slice(0, 3)
            .map(([key, val]) => (
              <div key={key} className="flex justify-between text-[11px]">
                <span className="text-text-secondary capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                <span className="text-text-primary font-mono">
                  {typeof val === "number" ? val.toFixed(2) : String(val)}
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* Confidence */}
      <div className="mb-5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10.5px] font-semibold uppercase tracking-widest text-text-tertiary">
            Confidence
          </span>
          <span className="text-xs font-mono font-bold text-accent">
            {(recommendation.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
          <div
            className="h-full bg-accent transition-all duration-300"
            style={{ width: `${recommendation.confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Apply button */}
      <button
        onClick={() => onApply(product.id, recommendation.recommended_price)}
        className="w-full px-3 py-2.5 bg-accent text-white rounded-lg font-medium text-sm hover:opacity-90 transition-opacity active:scale-98"
      >
        Apply ${recommendation.recommended_price.toFixed(2)}
      </button>
    </div>
  );
}
