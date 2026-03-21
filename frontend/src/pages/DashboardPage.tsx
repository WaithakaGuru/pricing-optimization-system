import { useState, useEffect } from "react";
import { dashboardApi } from "../api/client";
import { ErrorNotice, LoadingSkeleton } from "../components/common/LoadingUI";
import StatCard from "../components/dashboard/StatCard";
import RevenueChart from "../components/dashboard/RevenueChart";
import CategoryChart from "../components/dashboard/CategoryChart";
import PriceRecommendations from "../components/dashboard/PriceRecommendations";
import RecentTransactions from "../components/dashboard/RecentTransactions";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        const data = await dashboardApi.summary(30);
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load dashboard",
        );
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col gap-6 max-w-360">
        <LoadingSkeleton rows={4} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-6 max-w-360">
        <ErrorNotice message={error} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 md:gap-6 max-w-none px-0">
      {/* KPI row - responsive grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        <StatCard
          label="Revenue Today"
          value={`$${(metrics?.total_revenue || 0).toLocaleString("en-US", { maximumFractionDigits: 0 })}`}
          change={8.4}
          subtext="vs yesterday"
          accent
          delay={0}
        />
        <StatCard
          label="Transactions"
          value={`${metrics?.total_transactions || 0}`}
          change={5.1}
          subtext="vs yesterday"
          delay={60}
        />
        <StatCard
          label="Avg. Order Value"
          value={`$${(metrics?.average_order_value || 0).toFixed(2)}`}
          change={3.2}
          subtext="vs last week"
          delay={120}
        />
        <StatCard
          label="Inventory Health"
          value={`${((metrics?.inventory_health || 0) * 100).toFixed(0)}%`}
          change={-1.3}
          subtext="vs last month"
          delay={180}
        />
      </div>

      {/* Charts row - responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 md:gap-4">
        <div className="lg:col-span-2">
          <RevenueChart />
        </div>
        <div className="lg:col-span-1">
          <CategoryChart />
        </div>
      </div>

      {/* Bottom row - responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 md:gap-4">
        <div>
          <PriceRecommendations />
        </div>
        <div>
          <RecentTransactions />
        </div>
      </div>
    </div>
  );
}
