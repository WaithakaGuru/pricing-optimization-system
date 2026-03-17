import StatCard from '../components/dashboard/StatCard';
import RevenueChart from '../components/dashboard/RevenueChart';
import CategoryChart from '../components/dashboard/CategoryChart';
import PriceRecommendations from '../components/dashboard/PriceRecommendations';
import RecentTransactions from '../components/dashboard/RecentTransactions';

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6 max-w-[1440px]">

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Revenue Today"    value="$3,842"  change={8.4}  subtext="vs yesterday"  accent delay={0}   />
        <StatCard label="Transactions"     value="147"     change={5.1}  subtext="vs yesterday"         delay={60}  />
        <StatCard label="Avg. Order Value" value="$26.14"  change={3.2}  subtext="vs last week"         delay={120} />
        <StatCard label="Gross Margin"     value="54.8%"   change={-1.3} subtext="vs last month"        delay={180} />
      </div>

      {/* Charts row */}
      <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 320px' }}>
        <RevenueChart />
        <CategoryChart />
      </div>

      {/* Bottom row */}
      <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 360px' }}>
        <PriceRecommendations />
        <RecentTransactions />
      </div>

    </div>
  );
}
