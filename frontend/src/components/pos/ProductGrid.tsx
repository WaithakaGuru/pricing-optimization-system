import { useState } from "react";
import type { Product } from "../../types";

const CATEGORIES = ["All", "Coffee", "Tea", "Cold Brew", "Matcha"];

function getEmoji(name: string) {
  if (/coffee|espresso/i.test(name)) return "☕";
  if (/matcha/i.test(name)) return "🍃";
  if (/tea/i.test(name)) return "🍵";
  if (/cold|brew/i.test(name)) return "🧊";
  return "📦";
}

export default function ProductGrid({
  products,
  onAdd,
}: {
  products: Product[];
  onAdd: (p: Product) => void;
}) {
  const [cat, setCat] = useState("All");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = products.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) &&
      (cat === "All" || p.name.toLowerCase().includes(cat.toLowerCase())),
  );

  return (
    <div className="flex flex-col gap-3 h-full min-h-0">
      {/* Search */}
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary"
          width="13"
          height="13"
          viewBox="0 0 16 16"
          fill="none"
        >
          <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
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
          className="w-full h-10 pl-8 pr-3 border border-border rounded-lg bg-surface] text-sm text-text-primary placeholder:text-text-tertiary outline-none focus:border-accent transition-colors"
        />
      </div>

      {/* Category pills */}
      <div className="flex gap-1.5 flex-wrap">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setCat(c)}
            className={`px-3 py-1 rounded-full border text-xs font-medium transition-all ${
              cat === c
                ? "bg-[#2d3748] border-[#2d3748] text-white"
                : "bg-surface] border-border text-text-secondary hover:border-accent hover:text-accent"
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div
        className="grid gap-2.5 overflow-y-auto flex-1 py-3"
        style={{ gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))" }}
      >
        {filtered.map((p, i) => {
          const isExpanded = expandedId === p.id;
          return (
            <div
              key={p.id}
              className={`bg-surface] border-[1.5px] border-border rounded-xl p-3.5 flex flex-col gap-2 text-left transition-all duration-200 hover:border-accent ${isExpanded ? "shadow-lg" : "hover:shadow-md hover:-translate-y-px"} animate-fade-up`}
              style={{ animationDelay: `${i * 30}ms` }}
            >
              {/* Product Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <span className="text-3xl leading-none block mb-1">
                    {getEmoji(p.name)}
                  </span>
                  <span className="text-xs font-medium text-text-primary leading-snug">
                    {p.name}
                  </span>
                </div>
              </div>

              {/* Price */}
              <span className="text-sm font-semibold text-accent font-mono">
                ${p.current_price.toFixed(2)}
              </span>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="mt-2 pt-3 border-t border-border space-y-2 animate-fade-up">
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-text-tertiary">Cost:</span>
                      <span className="font-mono text-text-primary">
                        ${p.cost_price.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-tertiary">Margin:</span>
                      <span className="font-mono text-green-600">
                        {(
                          ((p.current_price - p.cost_price) / p.cost_price) *
                          100
                        ).toFixed(1)}
                        %
                      </span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-tertiary">Price Range:</span>
                      <span className="font-mono text-text-primary">
                        ${p.min_price.toFixed(2)} - ${p.max_price.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Buttons */}
              <div className="grid grid-cols-2 gap-2 mt-2">
                <button
                  onClick={() => onAdd(p)}
                  className="h-7 rounded bg-accent text-[#1a202c] text-xs font-semibold hover:opacity-90 transition-colors active:scale-95"
                >
                  Add to Cart
                </button>
                <button
                  onClick={() => setExpandedId(isExpanded ? null : p.id)}
                  className="h-7 rounded border border-border bg-surface-2] text-text-secondary text-xs font-semibold hover:border-accent hover:text-accent transition-colors"
                >
                  {isExpanded ? "See less" : "See Details"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
