import { useState, useEffect } from "react";
import { useAsync } from "../hooks";
import { pricesApi, productsApi } from "../api/client";
import type { PriceRecommendation } from "../types";

type SortBy = "name" | "change" | "confidence" | "current_price";
type AgentType = "sac" | "ppo" | "bandit";

// Skeleton Loader Component
function ProductCardSkeleton() {
  return (
    <div className="p-4 rounded-xl bg-surface border border-border animate-pulse">
      <div className="mb-3">
        <div className="h-4 bg-surface-2 rounded w-3/4 mb-2" />
        <div className="h-3 bg-surface-2 rounded w-1/3" />
      </div>
      <div className="space-y-2 mb-3">
        <div className="flex items-center justify-between">
          <div className="h-3 bg-surface-2 rounded w-1/4" />
          <div className="h-3 bg-surface-2 rounded w-1/5" />
        </div>
        <div className="flex items-center justify-between">
          <div className="h-3 bg-surface-2 rounded w-1/4" />
          <div className="h-3 bg-surface-2 rounded w-1/5" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 pt-3 border-t border-border">
        <div className="h-3 bg-surface-2 rounded" />
        <div className="h-3 bg-surface-2 rounded" />
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
  const {
    data: recommendations = [],
    loading: loadingRec,
    refetch: refetchRecommendations,
  } = useAsync(
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
  useEffect(() => {
    if (products?.length) {
      refetchRecommendations();
    }
  }, [products?.length, refetchRecommendations]);

  // Filter and sort products (hybrid: recommendations first, then all others)
  const allFiltered = (products || [])
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
    }));

  // Separate into two groups
  const withRecommendations = allFiltered
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

  const withoutRecommendations = allFiltered
    .filter((p) => !p.recommendation)
    .sort((a, b) => {
      if (sortBy === "name") {
        return a.name.localeCompare(b.name);
      }
      if (sortBy === "current_price") {
        return b.current_price - a.current_price;
      }
      return 0;
    });

  const filtered = [...withRecommendations, ...withoutRecommendations];
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
        <h1 className="text-3xl font-bold text-text-primary">
          Price Recommendations
        </h1>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Search Bar */}
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary"
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
            className="w-full pl-9 pr-3 py-2.5 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent text-text-primary"
          />
        </div>

        {/* Sort By */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortBy)}
          className="px-3 py-2.5 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent text-text-primary"
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
          className="px-3 py-2.5 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent text-text-primary"
        >
          <option value="sac">SAC Agent</option>
          <option value="ppo">PPO Agent</option>
          <option value="bandit">Bandit Agent</option>
        </select>

        {/* Count */}
        <div className="flex items-center justify-center px-3 py-2.5 bg-surface-2 border border-border rounded-lg text-sm text-text-secondary">
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
          <p className="text-text-tertiary">No products match your search</p>
        </div>
      ) : (
        <>
          {/* Section 1: Products with Recommendations */}
          {withRecommendations.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-text-primary mb-4">
                AI Price Recommendations ({withRecommendations.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                {withRecommendations.map((product) => {
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
                          ? "bg-accent-light border-2 border-accent shadow-md"
                          : "bg-surface border border-border hover:border-accent hover:shadow-md"
                      }`}
                    >
                      {/* Product Name and ID */}
                      <div className="mb-3">
                        <h3 className="font-semibold text-text-primary truncate">
                          {product.name}
                        </h3>
                        <p className="text-xs text-text-tertiary">
                          {product.id}
                        </p>
                      </div>

                      {/* Price Comparison */}
                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-text-tertiary">
                            Current
                          </span>
                          <span className="font-medium text-text-primary">
                            ${rec.current_price.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-accent">
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
                      <div className="grid grid-cols-2 gap-2 pt-3 border-t border-border">
                        <div>
                          <p className="text-xs text-text-tertiary">Change</p>
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
                          <p className="text-xs text-text-tertiary">
                            Confidence
                          </p>
                          <p className="text-sm font-semibold text-accent">
                            {(rec.confidence * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Section 2: Products without Recommendations */}
          {withoutRecommendations.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-text-primary mb-4">
                All Products ({withoutRecommendations.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {withoutRecommendations.map((product) => (
                  <button
                    key={product.id}
                    onClick={() => setSelectedProduct(product.id)}
                    className={`p-4 rounded-xl transition-all text-left ${
                      selectedProduct === product.id
                        ? "bg-blue-50 border-2 border-accent shadow-md"
                        : "bg-surface border border-border hover:border-accent hover:shadow-md"
                    }`}
                  >
                    {/* Product Name and ID */}
                    <div className="mb-3">
                      <h3 className="font-semibold text-text-primary truncate">
                        {product.name}
                      </h3>
                      <p className="text-xs text-text-tertiary">{product.id}</p>
                    </div>

                    {/* Current Price */}
                    <div className="space-y-2 mb-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-text-tertiary">
                          Current Price
                        </span>
                        <span className="font-medium text-text-primary">
                          ${product.current_price.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-text-tertiary">
                          Range
                        </span>
                        <span className="text-sm text-text-secondary">
                          ${product.min_price.toFixed(2)} - $
                          {product.max_price.toFixed(2)}
                        </span>
                      </div>
                    </div>

                    {/* Cost and Margin */}
                    <div className="grid grid-cols-2 gap-2 pt-3 border-t border-border">
                      <div>
                        <p className="text-xs text-text-tertiary">Cost</p>
                        <p className="text-sm font-semibold text-text-primary">
                          ${product.cost_price.toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-text-tertiary">Margin</p>
                        <p className="text-sm font-semibold text-green-600">
                          {(
                            ((product.current_price - product.cost_price) /
                              product.current_price) *
                            100
                          ).toFixed(0)}
                          %
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Detailed View - With Recommendation */}
      {selectedData && selectedData.recommendation && (
        <div className="bg-surface border border-border rounded-2xl shadow-xs p-6 mt-6">
          <h2 className="text-xl font-semibold text-text-primary mb-6">
            {selectedData.name} - Detailed Analysis
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-surface-2 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-text-tertiary mb-1">
                Current Price
              </div>
              <div className="text-2xl font-bold text-text-primary">
                ${selectedData.recommendation.current_price.toFixed(2)}
              </div>
            </div>
            <div className="bg-accent-light/50 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-accent mb-1">
                Recommended
              </div>
              <div className="text-2xl font-bold text-accent">
                ${selectedData.recommendation.recommended_price.toFixed(2)}
              </div>
            </div>
            <div className="bg-surface-2 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-text-tertiary mb-1">
                Agent
              </div>
              <div className="text-lg font-semibold text-text-primary">
                {selectedData.recommendation.agent.toUpperCase()}
              </div>
            </div>
            <div className="bg-surface-2 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-text-tertiary mb-1">
                Confidence
              </div>
              <div className="text-2xl font-bold text-text-primary">
                {(selectedData.recommendation.confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Factors */}
          {Object.keys(selectedData.recommendation.factors).length > 0 && (
            <div className="bg-surface-2 rounded-lg p-4">
              <h3 className="text-sm font-semibold uppercase tracking-widest text-text-tertiary mb-3">
                Decision Factors
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(selectedData.recommendation.factors).map(
                  ([key, value]) => (
                    <div key={key}>
                      <p className="text-xs text-text-tertiary capitalize mb-1">
                        {key.replace(/_/g, " ")}
                      </p>
                      <p className="text-sm font-semibold text-text-primary">
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

      {/* Detailed View - Without Recommendation */}
      {selectedData && !selectedData.recommendation && (
        <div className="bg-surface border border-border rounded-2xl shadow-xs p-6 mt-6">
          <h2 className="text-xl font-semibold text-text-primary mb-6">
            {selectedData.name} - Product Details
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-surface-2 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-text-tertiary mb-1">
                Current Price
              </div>
              <div className="text-2xl font-bold text-text-primary">
                ${selectedData.current_price.toFixed(2)}
              </div>
            </div>
            <div className="bg-surface-2 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-text-tertiary mb-1">
                Cost
              </div>
              <div className="text-2xl font-bold text-text-primary">
                ${selectedData.cost_price.toFixed(2)}
              </div>
            </div>
            <div className="bg-surface-2 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-text-tertiary mb-1">
                Margin
              </div>
              <div className="text-2xl font-bold text-green-600">
                {(
                  ((selectedData.current_price - selectedData.cost_price) /
                    selectedData.current_price) *
                  100
                ).toFixed(0)}
                %
              </div>
            </div>
            <div className="bg-surface-2 rounded-lg p-4 text-center">
              <div className="text-xs uppercase tracking-widest text-text-tertiary mb-1">
                Price Range
              </div>
              <div className="text-sm font-bold text-text-primary">
                ${selectedData.min_price.toFixed(2)} - $
                {selectedData.max_price.toFixed(2)}
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
            <p className="text-sm text-blue-900">
              No price recommendation available yet. The AI agent will analyze
              this product's performance and provide recommendations soon.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
