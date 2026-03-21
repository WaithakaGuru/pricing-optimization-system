interface Props {
  label: string;
  value: string;
  change?: number;
  subtext?: string;
  accent?: boolean;
  delay?: number;
}

export default function StatCard({
  label,
  value,
  change,
  subtext,
  accent,
  delay = 0,
}: Props) {
  const isPositive = change !== undefined && change >= 0;

  return (
    <div
      className={`rounded-2xl border p-6 flex flex-col gap-2 animate-fade-up transition-shadow hover:shadow-md ${
        accent
          ? "bg-accent border-accent"
          : "bg-surface border-border shadow-xs"
      }`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <span
        className={`text-[11px] font-semibold tracking-widest uppercase ${accent ? "text-white/70" : "text-[--color-text-tertiary]"}`}
      >
        {label}
      </span>

      <span
        className={`text-[28px] font-semibold tracking-tight leading-none font-mono ${accent ? "text-white" : "text-[--color-text-primary]"}`}
      >
        {value}
      </span>

      <div className="flex items-center gap-2">
        {change !== undefined && (
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              accent
                ? "bg-white/20 text-white"
                : isPositive
                  ? "bg-success-light text-success"
                  : "bg-danger-light text-danger"
            }`}
          >
            {isPositive ? "▲" : "▼"} {Math.abs(change).toFixed(1)}%
          </span>
        )}
        {subtext && (
          <span
            className={`text-xs ${accent ? "text-white/70" : "text-text-tertiary"}`}
          >
            {subtext}
          </span>
        )}
      </div>
    </div>
  );
}
