import React, { useState } from "react";
import { useAsync } from "../hooks";
import { pricesApi, productsApi } from "../api/client";
import type { PriceRecommendation } from "../types";

type SortBy = "name" | "change" | "confidence" | "current_price";
type AgentType = "sac" | "ppo" | "bandit";

// Skeleton Loader Component
function ProductCardSkeleton() {
  return (
    <div className="p-4 rounded-xl bg-[--color-surface] border border-[--color-border] animate-pulse">
      <div className="mb-3">
        <div className="h-4 bg-[--color-surface-2] rounded w-3/4 mb-2" />
        <div className="h-3 bg-[--color-surface-2] rounded w-1/3" />
      </div>
      <div className="space-y-2 mb-3">
        <div className="flex items-center justify-between">
          <div className="h-3 bg-[--color-surface-2] rounded w-1/4" />
          <div className="h-3 bg-[--color-surface-2] rounded w-1/5" />
        </div>
        <div className="flex items-center justify-between">
          <div className="h-3 bg-[--color-surface-2] rounded w-1/4" />
          <div className="h-3 bg-[--color-surface-2] rounded w-1/5" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 pt-3 border-t border-[--color-border]">
        <div className="h-3 bg-[--color-surface-2] rounded" />
        <div className="h-3 bg-[--color-surface-2] rounded" />
      </div>
    </div>
  );
}

export default function PricesPage() {
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("change");
  const [agent, setAgent] = useState<AgentType>("sac");
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);

  // Load products
  const {
    data: products = [],
    loading: loadingProducts,
    error: productsError,
  } = useAsync(() => productsApi.list(), true);

  // Load recommendations for displayed products
  const { data: recommendations = [], loading: loadingRec } = useAsync(
    async () => {
      if (!products?.length) return [];
      try {
        const recs = await Promise.all(
          products.map((p) => pricesApi.recommend(p.id).catch(() => null)),
        );
        return recs.filter((r): r is PriceRecommendation => r !== null);
      } catch {
        return [];
      }
    },
    false, // Don't auto-run; we'll trigger manually below
  );

  // Trigger recommendations fetch when products load
  const { refetch: refetchRecommendations } = useAsync(async () => null, false);

  React.useEffect(() => {
    if (products?.length) {
      refetchRecommendations();
    }
  }, [products?.length, refetchRecommendations]);

  // Filter and sort products
  const filtered = (products || [])
    .filter(
      (p) =>
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.id.toLowerCase().includes(search.toLowerCase()),
    )
    .map((p) => ({
      ...p,
      recommendation: (recommendations || []).find(
        (r) => r.product_id === p.id,
      ),
    }))
    .filter((p) => p.recommendation)
    .sort((a, b) => {
      if (sortBy === "name") {
        return a.name.localeCompare(b.name);
      }
      if (sortBy === "change" && a.recommendation && b.recommendation) {
        const changeA =
          ((a.recommendation.recommended_price -
            a.recommendation.current_price) /
            a.recommendation.current_price) *
          100;
        const changeB =
          ((b.recommendation.recommended_price -
            b.recommendation.current_price) /
            b.recommendation.current_price) *
          100;
        return Math.abs(changeB) - Math.abs(changeA);
      }
      if (sortBy === "confidence" && a.recommendation && b.recommendation) {
        return (
          (b.recommendation.confidence || 0) -
          (a.recommendation.confidence || 0)
        );
      }
      if (sortBy === "current_price") {
        return b.current_price - a.current_price;
      }
      return 0;
    });

  const selectedData = filtered.find((p) => p.id === selectedProduct);

  if (productsError) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading products</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-[--color-text-primary]">
          Price Recommendations
        </h1>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Search Bar */}
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[--color-text-tertiary]"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2.5 bg-[--color-surface] border border-[--color-border] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[--color-accent] text-[--color-text-primary]"
          />
        </div>

        {/* Sort By */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortBy)}
          className="px-3 py-2.5 bg-[--color-surface] border border-[--color-border] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[--color-accent] text-[--color-text-primary]"
        >
          <option value="change">Largest Change</option>
          <option value="confidence">Highest Confidence</option>
          <option value="current_price">Highest Price</option>
          <option value="name">Product Name</option>
        </select>

        {/* Agent Selection */}
        <select
          value={agent}
          onChange={(e) => setAgent(e.target.value as AgentType)}
          className="px-3 py-2.5 bg-[--color-surface] border border-[--color-border] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[--color-accent] text-[--color-text-primary]"
        >
          <option value="sac">SAC Agent</option>
          <option value="ppo">PPO Agent</option>
          <option value="bandit">Bandit Agent</option>
        </select>

        {/* Count */}
        <div className="flex items-center justify-center px-3 py-2.5 bg-[--color-surface-2] border border-[--color-border] rounded-lg text-sm text-[--color-text-secondary]">
          {filtered.length} product{filtered.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Recommendations Grid */}
      {loadingProducts || loadingRec ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-[--color-text-tertiary]">
            No products match your search
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((product) => {
            const rec = product.recommendation!;
            const changePercent =
              ((rec.recommended_price - rec.current_price) /
                rec.current_price) *
              100;
            const isPositive = changePercent > 0;

            return (
              <button
                key={product.id}
                onClick={() => setSelectedProduct(product.id)}
                className={`p-4 rounded-xl transition-all text-left ${
                  selectedProduct === product.id
                    ? "bg-[--color-accent-light] border-2 border-[--color-accent] shadow-md"
                    : "bg-[--color-surface] border border-[--color-border] hover:border-[--color-accent] hover:shadow-md"
                }`}
              >
                {/* Product Name and ID */}
                <div className="mb-3">
                  <h3 className="font-semibold text-[--color-text-primary] truncate">
                    {product.name}
                  </h3>
                  <p className="text-xs text-[--color-text-tertiary]">
                    {product.id}
                  </p>
                </div>

                {/* Price Comparison */}
                <div className="space-y-2 mb-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[--color-text-tertiary]">
                      Current
                    </span>
                    <span className="font-medium text-[--color-text-primary]">
                      ${rec.current_price.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[--color-accent]">
                      Recommended
                    </span>
                    <span
                      className={`font-semibold ${
                        isPositive ? "text-green-600" : "text-amber-600"
                      }`}
                    >
                      ${rec.recommended_price.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Change and Confidence */}
                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-[--color-border]">
                  <div>
                    <p className="text-xs text-[--color-text-tertiary]">
                      Change
                    </p>
                    <p
                      className={`text-sm font-semibold ${
                        isPositive ? "text-green-600" : "text-amber-600"
                      }`}
                    >
                      {isPositive ? "+" : ""}
                      {changePercent.toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[--color-text-tertiary]">
                      Confidence
                    </p>
                    <p className="text-sm font-semibold text-[--color-accent]">
                      {(rec.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Detailed View */}
      {selectedData && selectedData.recommendation && (
        <div className="bg-[--color-surface] border border-[--color-border] rounded-2xl shadow-xs p-6 mt-6">
          <h2 className="text-xl font-semibold text-[--color-text-primary] mb-6">
            {selectedData.name} - Detailed Analysis
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-[--color-surface-2] rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-[--color-text-tertiary] mb-1">
                Current Price
              </div>
              <div className="text-2xl font-bold text-[--color-text-primary]">
                ${selectedData.recommendation.current_price.toFixed(2)}
              </div>
            </div>
            <div className="bg-[--color-accent-light]/50 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-[--color-accent] mb-1">
                Recommended
              </div>
              <div className="text-2xl font-bold text-[--color-accent]">
                ${selectedData.recommendation.recommended_price.toFixed(2)}
              </div>
            </div>
            <div className="bg-[--color-surface-2] rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-[--color-text-tertiary] mb-1">
                Agent
              </div>
              <div className="text-lg font-semibold text-[--color-text-primary]">
                {selectedData.recommendation.agent.toUpperCase()}
              </div>
            </div>
            <div className="bg-[--color-surface-2] rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-[--color-text-tertiary] mb-1">
                Confidence
              </div>
              <div className="text-2xl font-bold text-[--color-text-primary]">
                {(selectedData.recommendation.confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Factors */}
          {Object.keys(selectedData.recommendation.factors).length > 0 && (
            <div className="bg-[--color-surface-2] rounded-lg p-4">
              <h3 className="text-sm font-semibold uppercase tracking-widest text-[--color-text-tertiary] mb-3">
                Decision Factors
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(selectedData.recommendation.factors).map(
                  ([key, value]) => (
                    <div key={key}>
                      <p className="text-xs text-[--color-text-tertiary] capitalize mb-1">
                        {key.replace(/_/g, " ")}
                      </p>
                      <p className="text-sm font-semibold text-[--color-text-primary]">
                        {String(value)}
                      </p>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
