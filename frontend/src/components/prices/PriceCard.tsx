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
      <div className="bg-[--color-surface] border border-[--color-border] rounded-xl p-5 animate-pulse">
        <div className="h-4 bg-[--color-surface-2] rounded w-3/4 mb-3" />
        <div className="h-10 bg-[--color-surface-2] rounded w-1/2" />
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

  return (
    <div className="bg-[--color-surface] border border-[--color-border] rounded-xl p-5 hover:border-[--color-accent] transition-colors animate-fade-up">
      {/* Product name */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-[--color-text-primary] truncate leading-tight mb-1">
          {product.name}
        </h3>
        <p className="text-[11px] text-[--color-text-tertiary]">
          ${product.cost_price.toFixed(2)} cost
        </p>
      </div>

      {/* Current price */}
      <div className="mb-4">
        <span className="text-[10.5px] font-semibold uppercase tracking-widest text-[--color-text-tertiary]">
          Current
        </span>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-[--color-text-primary]">
            ${product.current_price.toFixed(2)}
          </span>
          <span className="text-[11px] text-[--color-text-tertiary]">
            {margin.toFixed(1)}% margin
          </span>
        </div>
      </div>

      {/* Recommended price */}
      <div className="mb-5 p-3 bg-[--color-accent-light] border border-[--color-accent] rounded-lg">
        <span className="text-[10.5px] font-semibold uppercase tracking-widest text-[--color-accent] block mb-1">
          Recommended
        </span>
        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-2xl font-bold text-[--color-accent]">
            ${recommendation.recommended_price.toFixed(2)}
          </span>
          <span
            className={`text-xs font-bold font-mono ${diff >= 0 ? "text-[--color-success]" : "text-[--color-danger]"}`}
          >
            {diff >= 0 ? "+" : ""}
            {pctChange.toFixed(1)}%
          </span>
        </div>
        <span className="text-[11px] text-[--color-accent]">
          {newMargin.toFixed(1)}% margin
        </span>
      </div>

      {/* Factors */}
      <div className="mb-4 p-3 bg-[--color-surface-2] rounded-lg">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-[--color-text-tertiary] block mb-2">
          Factors
        </span>
        <div className="space-y-1">
          {Object.entries(recommendation.factors)
            .slice(0, 3)
            .map(([key, val]) => (
              <div key={key} className="flex justify-between text-[11px]">
                <span className="text-[--color-text-secondary] capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                <span className="text-[--color-text-primary] font-mono">
                  {typeof val === "number" ? val.toFixed(2) : String(val)}
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* Confidence */}
      <div className="mb-5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10.5px] font-semibold uppercase tracking-widest text-[--color-text-tertiary]">
            Confidence
          </span>
          <span className="text-xs font-mono font-bold text-[--color-accent]">
            {(recommendation.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-[--color-surface-2] rounded-full overflow-hidden">
          <div
            className="h-full bg-[--color-accent] transition-all duration-300"
            style={{ width: `${recommendation.confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Apply button */}
      <button
        onClick={() => onApply(product.id, recommendation.recommended_price)}
        className="w-full px-3 py-2.5 bg-[--color-accent] text-white rounded-lg font-medium text-sm hover:opacity-90 transition-opacity active:scale-98"
      >
        Apply ${recommendation.recommended_price.toFixed(2)}
      </button>
    </div>
  );
}
