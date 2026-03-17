import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { generateCategoryData } from '../../api/mock';

export default function CategoryChart() {
  const data = generateCategoryData();
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="bg-[--color-surface] border border-[--color-border] rounded-2xl p-6 shadow-xs h-full">
      <h2 className="text-sm font-semibold text-[--color-text-primary] mb-5">Revenue by Category</h2>
      <div className="flex items-center gap-5">
        <ResponsiveContainer width={150} height={150}>
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={48} outerRadius={68} paddingAngle={3} dataKey="value">
              {data.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
            </Pie>
            <Tooltip
              formatter={(val: number) => [`${((val / total) * 100).toFixed(0)}%`, '']}
              contentStyle={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: 12 }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex flex-col gap-2.5 flex-1">
          {data.map((d) => (
            <div key={d.name} className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: d.color }} />
              <span className="flex-1 text-xs text-[--color-text-secondary]">{d.name}</span>
              <span className="text-xs font-semibold text-[--color-text-primary] font-mono">{d.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
