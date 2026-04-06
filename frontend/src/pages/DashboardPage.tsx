import { useAsync } from "../hooks";
import { posApi } from "../api/client";
import { MOCK_PRODUCTS, MOCK_TRANSACTIONS } from "../api/mock";
import StatCard from "../components/dashboard/StatCard";
import RevenueChart from "../components/dashboard/RevenueChart";
import CategoryChart from "../components/dashboard/CategoryChart";
import PriceRecommendations from "../components/dashboard/PriceRecommendations";
import RecentTransactions from "../components/dashboard/RecentTransactions";

export default function DashboardPage() {
  const { data: stats } = useAsync(
    () =>
      posApi.stats().catch(() => ({
        revenue_today: 3842,
        transactions: 147,
        avg_order_value: 26.14,
        gross_margin: 54.8,
      })),
    true,
  );

  const { data: transactions } = useAsync(
    () => posApi.transactions(10).catch(() => MOCK_TRANSACTIONS.slice(0, 10)),
    true,
  );

  const currentStats = stats || {
    revenue_today: 3842,
    transactions: 147,
    avg_order_value: 26.14,
    gross_margin: 54.8,
  };

  const recommendations = MOCK_PRODUCTS.slice(0, 3).map((p) => ({
    product_id: p.id,
    current_price: p.current_price,
    recommended_price: p.current_price * (0.95 + Math.random() * 0.1),
    confidence: 0.75 + Math.random() * 0.2,
    agent: "sac",
    factors: { demand: "High", seasonality: "Positive" },
    timestamp: new Date().toISOString(),
  }));

  return (
    <div className="flex flex-col gap-6 max-w-360">
      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Revenue Today"
          value={`$${currentStats.revenue_today?.toLocaleString() || "0"}`}
          change={8.4}
          subtext="vs yesterday"
          accent
          delay={0}
        />
        <StatCard
          label="Transactions"
          value={String(currentStats.transactions || 0)}
          change={5.1}
          subtext="vs yesterday"
          delay={60}
        />
        <StatCard
          label="Avg. Order Value"
          value={`$${(currentStats.avg_order_value || 0).toFixed(2)}`}
          change={3.2}
          subtext="vs last week"
          delay={120}
        />
        <StatCard
          label="Gross Margin"
          value={`${(currentStats.gross_margin || 0).toFixed(1)}%`}
          change={-1.3}
          subtext="vs last month"
          delay={180}
        />
      </div>

      {/* Charts row */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 320px" }}>
        <RevenueChart />
        <CategoryChart />
      </div>

      {/* Bottom row */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 360px" }}>
        <PriceRecommendations recommendations={recommendations} />
        <RecentTransactions
          transactions={transactions || MOCK_TRANSACTIONS.slice(0, 10)}
        />
      </div>
    </div>
  );
}
