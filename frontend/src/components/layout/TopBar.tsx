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
    <header className="h-16 md:h-18 bg-white border-b border-border-2 flex items-center justify-between px-4 md:px-7 sticky top-0 z-40 shadow-sm">
      <div className="flex items-baseline gap-2 md:gap-3 min-w-0">
        <h1 className="text-lg md:text-xl font-semibold text-[--color-text-primary] tracking-tight truncate">
          {meta.title}
        </h1>
        {meta.sub && (
          <span className="hidden sm:inline text-xs md:text-sm text-[--color-text-tertiary] truncate">
            {meta.sub}
          </span>
        )}
      </div>
      <div className="flex items-center gap-2 md:gap-3.5 shrink-0">
        <span className="hidden sm:inline text-xs text-[--color-text-tertiary]">
          {now}
        </span>
        <div className="w-8 h-8 rounded-full bg-accent text-white text-xs font-semibold flex items-center justify-center shrink-0">
          A
        </div>
      </div>
    </header>
  );
}
