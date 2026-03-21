export function ErrorNotice({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex items-center gap-2.5 px-4 py-3 bg-[--color-danger-light] border border-red-200 rounded-xl text-[--color-danger] text-sm animate-fade-up">
      <svg
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
        className="shrink-0"
      >
        <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.4" />
        <path
          d="M8 4v4M8 11v.5"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
      <span className="flex-1">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs font-medium text-[--color-danger] border border-current px-2.5 py-1 rounded hover:bg-red-100 transition-colors whitespace-nowrap"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-[--color-accent] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {[...Array(rows)].map((_, i) => (
        <div
          key={i}
          className="h-12 bg-[--color-surface-2] rounded-lg animate-pulse"
        />
      ))}
    </div>
  );
}
