import { useLocation } from "react-router-dom";

const TITLES: Record<string, { title: string; sub: string }> = {
  "/": { title: "Dashboard", sub: "KPIs, revenue & pricing overview" },
  "/pos": { title: "POS Terminal", sub: "Record sales and transactions" },
  "/inventory": { title: "Inventory", sub: "Stock levels and reorder alerts" },
};

export default function TopBar() {
  const { pathname } = useLocation();
  const meta = TITLES[pathname] ?? { title: "OPTIMA", sub: "" };
  const now = new Date().toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <header className="h-18 bg-white border-b border-[--color-border] flex items-center justify-between px-7 sticky top-0 z-40 shadow-sm">
      <div className="flex items-baseline gap-3">
        <h1 className="text-xl font-semibold text-[--color-text-primary] tracking-tight">
          {meta.title}
        </h1>
        {meta.sub && (
          <span className="text-sm text-[--color-text-tertiary]">
            {meta.sub}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3.5">
        <span className="text-xs text-[--color-text-tertiary]">{now}</span>
        <div className="w-8 h-8 rounded-full bg-[--color-accent] text-text-secondary text-sm font-semibold flex items-center justify-center">
          A
        </div>
      </div>
    </header>
  );
}
