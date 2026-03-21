import { MOCK_TRANSACTIONS } from "../../api/mock";

export default function RecentTransactions() {
  const txns = MOCK_TRANSACTIONS.slice(0, 8);
  return (
    <div className="bg-[--color-surface] border border-[--color-border] rounded-2xl shadow-xs overflow-hidden">
      <div className="flex items-center justify-between px-6 py-5 border-b border-[--color-border]">
        <h2 className="text-sm font-semibold text-[--color-text-primary]">
          Recent Transactions
        </h2>
        <a
          href="/pos"
          className="text-xs font-medium text-[--color-accent] hover:opacity-75 transition-opacity"
        >
          View all →
        </a>
      </div>
      <div>
        {txns.map((t, i) => {
          const item = t.items[0];
          const time = new Date(t.timestamp).toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          });
          const date = new Date(t.timestamp).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          });
          return (
            <div
              key={t.id}
              className="flex items-center gap-3 px-6 py-2.5 border-b border-[--color-border] last:border-0 hover:bg-[--color-surface-2] transition-colors animate-fade-up"
              style={{ animationDelay: `${i * 35}ms` }}
            >
              <div className="w-8 h-8 rounded-lg bg-[--color-accent-light] text-[--color-accent] flex items-center justify-center shrink-0">
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
                  <path
                    d="M1 1h2l2 8h7l2-5H4"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <circle cx="7" cy="13.5" r="1" fill="currentColor" />
                  <circle cx="12" cy="13.5" r="1" fill="currentColor" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-medium text-[--color-text-primary] truncate">
                  {item?.product_name ?? "Unknown"}
                </p>
                <p className="text-[11px] text-[--color-text-tertiary]">
                  {item?.quantity ?? 1} × ${item?.price.toFixed(2)} · {date}{" "}
                  {time}
                </p>
              </div>
              <span className="text-sm font-semibold text-[--color-text-primary] font-mono shrink-0">
                ${t.total.toFixed(2)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
