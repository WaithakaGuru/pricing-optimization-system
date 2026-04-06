import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

interface CategoryChartProps {
  data?: Array<{ name: string; value: number; color: string }>;
}

export default function CategoryChart({ data = [] }: CategoryChartProps) {
  return (
    <div className="bg-surface border border-border rounded-2xl p-6 shadow-xs h-full">
      <h2 className="text-sm font-semibold text-text-primary mb-5">
        Revenue by Category
      </h2>
      <div className="flex items-center gap-5">
        <ResponsiveContainer width={150} height={150}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={68}
              paddingAngle={3}
              dataKey="value"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(val) => [
                `$${(Number(val) || 0).toLocaleString("en-US", { maximumFractionDigits: 2 })}`,
                "",
              ]}
              contentStyle={{
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex flex-col gap-2.5 flex-1">
          {data.map((d) => (
            <div key={d.name} className="flex items-center gap-2">
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ background: d.color }}
              />
              <span className="flex-1 text-xs text-text-secondary">
                {d.name}
              </span>
              <span className="text-xs font-semibold text-text-primary font-mono">
                $
                {typeof d.value === "string"
                  ? d.value
                  : d.value.toLocaleString("en-US", {
                      maximumFractionDigits: 0,
                    })}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
