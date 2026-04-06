import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
// import type { TimeRange } from '../../types';

interface RevenueChartProps {
  data?: Array<{ date: string; revenue: number; transactions: number }>;
}

export default function RevenueChart({ data = [] }: RevenueChartProps) {
  return (
    <div className="bg-[--color-surface] border border-[--color-border] rounded-2xl p-6 shadow-xs">
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-sm font-semibold text-[--color-text-primary]">
            Revenue
          </h2>
          <p className="text-xs text-[--color-text-tertiary] mt-0.5">
            $
            {data.length > 0
              ? data.reduce((s, d) => s + d.revenue, 0).toLocaleString()
              : "0"}{" "}
            total · $
            {data.length > 0
              ? Math.round(
                  data.reduce((s, d) => s + d.revenue, 0) / data.length,
                )
              : "0"}
            /day avg
          </p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={210}>
        <AreaChart
          data={data}
          margin={{ top: 4, right: 4, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#1A56FF" stopOpacity={0.14} />
              <stop offset="95%" stopColor="#1A56FF" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--color-border)" />
          <XAxis
            dataKey="date"
            tick={{
              fontSize: 11,
              fill: "var(--color-text-tertiary)",
              fontFamily: "DM Sans",
            }}
            axisLine={false}
            tickLine={false}
            interval={Math.floor(data.length / 6)}
          />
          <YAxis
            tick={{
              fontSize: 11,
              fill: "var(--color-text-tertiary)",
              fontFamily: "DM Mono",
            }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
            width={46}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="revenue"
            stroke="#1A56FF"
            strokeWidth={2}
            fill="url(#revGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[--color-surface] border border-[--color-border] rounded-lg px-3 py-2 shadow-lg text-xs">
      <p className="text-[--color-text-tertiary] mb-1">{label}</p>
      <p className="text-sm font-semibold text-[--color-text-primary] font-mono">
        ${payload[0].value.toLocaleString()}
      </p>
      <p className="text-[--color-text-tertiary]">
        {payload[0].payload.transactions} transactions
      </p>
    </div>
  );
}
