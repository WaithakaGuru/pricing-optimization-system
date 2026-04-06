import type { PriceRecommendation } from "../../types";

interface Props {
  recommendations: PriceRecommendation[];
}

export default function PriceRecommendations({ recommendations }: Props) {
  return (
    <div className="bg-surface border border-border rounded-2xl shadow-xs overflow-hidden">
      <div className="flex items-center gap-2.5 px-6 py-5 border-b border-border">
        <h2 className="text-sm font-semibold text-text-primary">
          AI Price Recommendations
        </h2>
        <span className="text-[10.5px] font-semibold text-success bg-success-light px-2 py-0.5 rounded-full tracking-wide">
          Live
        </span>
      </div>

      {/* Header row */}
      <div
        className="grid px-6 py-2 border-b border-border bg-surface-2 text-[11px] font-semibold uppercase tracking-widest text-text-tertiary"
        style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr 1.2fr 80px" }}
      >
        <span>Product</span>
        <span>Current</span>
        <span>Recommended</span>
        <span>Change</span>
        <span>Confidence</span>
        <span></span>
      </div>

      {recommendations.length === 0 ? (
        <div className="px-6 py-8 text-center text-text-tertiary">
          <p className="text-sm">No recommendations available</p>
        </div>
      ) : (
        recommendations.map((r, i) => {
          const diff = r.recommended_price - r.current_price;
          const pct = (diff / r.current_price) * 100;
          return (
            <div
              key={r.product_id}
              className="grid items-center px-6 py-3 border-b border-border last:border-0 hover:bg-surface transition-colors animate-fade-up"
              style={{
                gridTemplateColumns: "2fr 1fr 1fr 1fr 1.2fr 80px",
                animationDelay: `${i * 40}ms`,
              }}
            >
              <span className="text-[13.5px] text-text-primary truncate pr-4">
                {r.product_id}
              </span>
              <span className="text-sm text-text-secondary font-mono">
                ${r.current_price.toFixed(2)}
              </span>
              <span className="text-sm text-text-secondary font-mono">
                ${r.recommended_price.toFixed(2)}
              </span>
              <span
                className={`text-xs font-semibold font-mono ${diff >= 0 ? "text-success" : "text-danger"}`}
              >
                {diff >= 0 ? "+" : ""}
                {pct.toFixed(1)}%
              </span>
              <div className="flex items-center gap-2 pr-2">
                <div className="flex-1 h-1 bg-[--color-surface-2] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all duration-500"
                    style={{ width: `${r.confidence * 100}%` }}
                  />
                </div>
                <span className="text-[11px] text-[--color-text-tertiary] font-mono w-7 text-right">
                  {(r.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <button className="text-xs font-medium text-accent border border-accent px-3 py-1.5 rounded hover:bg-accent hover:text-white transition-colors">
                Apply
              </button>
            </div>
          );
        })
      )}
    </div>
  );
}
