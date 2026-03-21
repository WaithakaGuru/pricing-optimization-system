interface Props {
  qty: number;
  reorder: number;
  max?: number;
}

export default function StockBar({ qty, reorder, max }: Props) {
  const cap = max ?? Math.max(qty * 1.4, reorder * 4);
  const pct = Math.min(100, (qty / cap) * 100);
  const reorderPct = Math.min(100, (reorder / cap) * 100);
  const color =
    qty <= reorder * 0.5
      ? "#E03E3E"
      : qty <= reorder
        ? "#D97706"
        : qty >= reorder * 6
          ? "#1A56FF"
          : "#12A169";

  return (
    <div className="flex items-center gap-2.5">
      <div className="flex-1 h-1.5 bg-red-700 rounded-full relative">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: color }}
        />
        <div
          className="absolute -top-0.75 w-px h-3 bg-border-2 rounded-sm"
          style={{ left: `${reorderPct}%`, transform: "translateX(-50%)" }}
        />
      </div>
      <span className="text-xs text-text-secondary font-mono w-8 text-right shrink-0">
        {qty}
      </span>
    </div>
  );
}
