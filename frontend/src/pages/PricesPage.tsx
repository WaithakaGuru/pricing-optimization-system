import { useState, useEffect } from "react";
import { pricesApi, productsApi } from "../api/client";
import type { Product, PriceRecommendation } from "../types";
import PriceCard from "../components/prices/PriceCard";
import PriceFilters from "../components/prices/PriceFilters";

type AgentType = "ppo" | "sac" | "bandit";

export default function PricesPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [recommendations, setRecommendations] = useState<
    Record<string, PriceRecommendation>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agent, setAgent] = useState<AgentType>("ppo");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"current" | "recommended" | "change">(
    "change",
  );

  // Fetch products on mount
  useEffect(() => {
    async function loadProducts() {
      try {
        setLoading(true);
        const data = await productsApi.list();
        setProducts(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load products",
        );
      } finally {
        setLoading(false);
      }
    }
    loadProducts();
  }, []);

  // Fetch recommendations when agent changes or products load
  useEffect(() => {
    if (products.length === 0) return;

    async function loadRecommendations() {
      try {
        setLoading(true);
        const recs: Record<string, PriceRecommendation> = {};

        for (const product of products) {
          try {
            const rec = await pricesApi.recommend(product.id);
            recs[product.id] = rec;
          } catch (err) {
            console.error(
              `Failed to get recommendation for ${product.id}`,
              err,
            );
          }
        }

        setRecommendations(recs);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load recommendations",
        );
      } finally {
        setLoading(false);
      }
    }

    loadRecommendations();
  }, [products, agent]);

  // Filter and sort products
  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()),
  );

  const sorted = [...filtered].sort((a, b) => {
    const recA = recommendations[a.id];
    const recB = recommendations[b.id];

    if (!recA || !recB) return 0;

    switch (sortBy) {
      case "current":
        return a.current_price - b.current_price;
      case "recommended":
        return recA.recommended_price - recB.recommended_price;
      case "change":
        return (
          recB.recommended_price -
          b.current_price -
          (recA.recommended_price - a.current_price)
        );
      default:
        return 0;
    }
  });

  const handleApplyPrice = async (productId: string, newPrice: number) => {
    try {
      await pricesApi.apply(productId, newPrice);
      // Refresh products to show updated price
      const updated = await productsApi.list();
      setProducts(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply price");
    }
  };

  if (loading && products.length === 0) {
    return (
      <div className="flex flex-col gap-6 max-w-[1400px]">
        <div className="h-12 bg-[--color-surface-2] rounded-lg animate-pulse" />
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
          }}
        >
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-64 bg-[--color-surface-2] rounded-xl animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 max-w-[1400px]">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[--color-text-primary] mb-1">
          AI Price Recommendations
        </h1>
        <p className="text-sm text-[--color-text-tertiary]">
          Optimize prices using ML agents
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2.5 px-4 py-3 bg-[--color-danger-light] border border-red-200 rounded-xl text-[--color-danger] text-sm animate-fade-up">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            className="flex-shrink-0"
          >
            <circle
              cx="8"
              cy="8"
              r="7"
              stroke="currentColor"
              strokeWidth="1.4"
            />
            <path
              d="M8 4v4M8 11v.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <span className="flex-1">{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-[--color-danger] opacity-60 hover:opacity-100"
          >
            ✕
          </button>
        </div>
      )}

      {/* Filters */}
      <PriceFilters
        agent={agent}
        onAgentChange={setAgent}
        search={search}
        onSearchChange={setSearch}
        sortBy={sortBy}
        onSortByChange={setSortBy}
      />

      {/* Products grid */}
      {sorted.length === 0 ? (
        <div className="flex items-center justify-center h-64 bg-[--color-surface] border border-[--color-border] rounded-xl text-[--color-text-tertiary]">
          <p>No products found</p>
        </div>
      ) : (
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
          }}
        >
          {sorted.map((product) => (
            <PriceCard
              key={product.id}
              product={product}
              recommendation={recommendations[product.id]}
              onApply={handleApplyPrice}
            />
          ))}
        </div>
      )}
    </div>
  );
}
