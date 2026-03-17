interface Props {
  label: string;
  value: string;
  change?: number;
  subtext?: string;
  accent?: boolean;
  delay?: number;
}

export default function StatCard({ label, value, change, subtext, accent, delay = 0 }: Props) {
  const isPositive = change !== undefined && change >= 0;

  return (
    <div
      className={`rounded-2xl border p-6 flex flex-col gap-2 animate-fade-up transition-shadow hover:shadow-md ${
        accent
          ? 'bg-[--color-accent] border-[--color-accent] text-white'
          : 'bg-[--color-surface] border-[--color-border] shadow-xs'
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <span className={`text-[11px] font-semibold tracking-widest uppercase ${accent ? 'text-white/70' : 'text-[--color-text-tertiary]'}`}>
        {label}
      </span>

      <span className={`text-[28px] font-semibold tracking-tight leading-none font-mono ${accent ? 'text-white' : 'text-[--color-text-primary]'}`}>
        {value}
      </span>

      <div className="flex items-center gap-2">
        {change !== undefined && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
            accent
              ? 'bg-white/20 text-white'
              : isPositive
                ? 'bg-[--color-success-light] text-[--color-success]'
                : 'bg-[--color-danger-light] text-[--color-danger]'
          }`}>
            {isPositive ? '▲' : '▼'} {Math.abs(change).toFixed(1)}%
          </span>
        )}
        {subtext && (
          <span className={`text-xs ${accent ? 'text-white/60' : 'text-[--color-text-tertiary]'}`}>
            {subtext}
          </span>
        )}
      </div>
    </div>
  );
}
