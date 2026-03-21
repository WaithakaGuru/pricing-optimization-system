import { useState, useEffect } from "react";
import type { Transaction } from "../../types";
import { posApi } from "../../api/client";

export default function RecentTransactions() {
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const data = await posApi.transactions(50);
        // Sort by timestamp descending (newest first)
        const sorted = (data as Transaction[]).sort(
          (a, b) =>
            new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
        );
        setTxns(sorted.slice(0, 15)); // Show top 15 most recent
      } catch (err) {
        console.error("Error fetching transactions:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
    // Load on mount only - no periodic polling
  }, []);

  if (loading && txns.length === 0) {
    return (
      <div className="bg-surface] border border-border rounded-2xl shadow-xs overflow-hidden">
        <div className="px-6 py-5 flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface] border border-border rounded-2xl shadow-xs overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-6 py-5 border-b border-border shrink-0">
        <h2 className="text-sm font-semibold text-text-primary">
          Recent Transactions
        </h2>
        <a
          href="/pos"
          className="text-xs font-medium text-accent hover:opacity-75 transition-opacity"
        >
          View all →
        </a>
      </div>
      <div className="overflow-y-auto flex-1 max-h-96">
        {txns.length === 0 ? (
          <div className="px-6 py-8 text-center text-text-tertiary">
            <p className="text-sm">No transactions yet</p>
          </div>
        ) : (
          txns.map((t, i) => {
            const item = t.items?.[0];
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
                className="flex items-center gap-3 px-6 py-2.5 border-b border-border last:border-0 hover:bg-surface-2] transition-colors animate-fade-up"
                style={{ animationDelay: `${i * 35}ms` }}
              >
                <div className="w-8 h-8 rounded-lg bg-accent-light text-accent flex items-center justify-center shrink-0">
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
                  <p className="text-[13px] font-medium text-text-primary truncate">
                    {item?.product_name ?? "Unknown"}
                  </p>
                  <p className="text-[11px] text-text-tertiary">
                    {item?.quantity ?? 1} × $
                    {item?.price ? item.price.toFixed(2) : "0.00"} · {date}{" "}
                    {time}
                  </p>
                </div>
                <span className="text-sm font-semibold text-text-primary font-mono shrink-0">
                  ${t.total.toFixed(2)}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
