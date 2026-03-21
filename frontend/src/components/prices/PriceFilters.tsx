interface PriceFiltersProps {
  agent: "ppo" | "sac" | "bandit";
  onAgentChange: (agent: "ppo" | "sac" | "bandit") => void;
  search: string;
  onSearchChange: (search: string) => void;
  sortBy: "current" | "recommended" | "change";
  onSortByChange: (sortBy: "current" | "recommended" | "change") => void;
}

export default function PriceFilters({
  agent,
  onAgentChange,
  search,
  onSearchChange,
  sortBy,
  onSortByChange,
}: PriceFiltersProps) {
  const agents = [
    { value: "ppo", label: "PPO Agent", desc: "Policy gradient" },
    { value: "sac", label: "SAC Agent", desc: "Off-policy" },
    { value: "bandit", label: "Bandit", desc: "Multi-armed" },
  ] as const;

  const sorts = [
    { value: "change", label: "Largest Change" },
    { value: "recommended", label: "Recommended Price" },
    { value: "current", label: "Current Price" },
  ] as const;

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative max-w-xs">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 text-[--color-text-tertiary]"
          width="13"
          height="13"
          viewBox="0 0 16 16"
          fill="none"
        >
          <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
          <path
            d="M11 11l3 3"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
        <input
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search products…"
          className="w-full h-9 pl-8 pr-3 border border-[--color-border] rounded-lg bg-[--color-surface] text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] outline-none focus:border-[--color-accent] transition-colors"
        />
      </div>

      {/* Controls row */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Agent selector */}
        <div className="flex gap-2">
          {agents.map(({ value, label, desc }) => (
            <button
              key={value}
              onClick={() => onAgentChange(value)}
              className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                agent === value
                  ? "bg-accent text-white border-[--color-accent]"
                  : "bg-surface border-[--color-border] text-[--color-text-secondary] hover:border-[--color-accent]"
              }`}
              title={desc}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Sort selector */}
        <select
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value as typeof sortBy)}
          className="px-3 py-1.5 rounded-lg border border-[--color-border] bg-[--color-surface] text-xs font-medium text-[--color-text-primary] outline-none focus:border-[--color-accent] cursor-pointer"
        >
          {sorts.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
