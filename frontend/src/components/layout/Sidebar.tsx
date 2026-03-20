import { NavLink } from "react-router-dom";

const NAV = [
  {
    group: "OVERVIEW",
    items: [{ to: "/", icon: <GridIcon />, label: "Dashboard" }],
  },
  {
    group: "PRICING",
    items: [{ to: "/prices", icon: <PricingIcon />, label: "Price Optimizer" }],
  },
  {
    group: "OPERATIONS",
    items: [
      { to: "/pos", icon: <PosIcon />, label: "POS Terminal" },
      { to: "/inventory", icon: <BoxIcon />, label: "Inventory" },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside
      className="fixed top-0 left-0 w-58 h-screen bg-[--color-surface] border-r border-[--color-border] flex flex-col z-50"
      style={{ width: "232px" }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[--color-border]">
        <div className="w-8 h-8 rounded-lg bg-[--color-accent] text-white flex items-center justify-center text-sm font-bold tracking-tight shrink-0">
          O
        </div>
        <span className="text-sm font-semibold tracking-widest text-[--color-text-primary]">
          OPTIMA
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 flex flex-col gap-6 overflow-y-auto">
        {NAV.map((group) => (
          <div key={group.group} className="flex flex-col gap-0.5">
            <span className="text-[10px] font-semibold tracking-widest text-[--color-text-tertiary] px-2 pb-1.5 uppercase">
              {group.group}
            </span>
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-2.5 py-2 rounded-md text-[13.5px] font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-[#2d3748] text-[#e2e8f0] shadow-md ring-2 ring-[#2d3748] ring-opacity-30"
                      : "text-[--color-text-secondary] hover:bg-[--color-surface-2] hover:text-[--color-text-primary]"
                  }`
                }
              >
                <span className="shrink-0">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="flex items-center gap-2 px-5 py-3.5 border-t border-[--color-border]">
        <div className="w-1.5 h-1.5 rounded-full bg-[--color-border-2] shrink-0" />
        <span className="text-xs text-[--color-text-tertiary]">
          Backend offline
        </span>
      </div>
    </aside>
  );
}

function GridIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <rect
        x="1"
        y="1"
        width="6"
        height="6"
        rx="1.5"
        fill="currentColor"
        opacity=".75"
      />
      <rect
        x="9"
        y="1"
        width="6"
        height="6"
        rx="1.5"
        fill="currentColor"
        opacity=".75"
      />
      <rect
        x="1"
        y="9"
        width="6"
        height="6"
        rx="1.5"
        fill="currentColor"
        opacity=".75"
      />
      <rect
        x="9"
        y="9"
        width="6"
        height="6"
        rx="1.5"
        fill="currentColor"
        opacity=".75"
      />
    </svg>
  );
}
function PricingIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.4" />
      <path
        d="M8 4.5v7M5.5 6h5M5.5 10h5"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}
function PosIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <rect
        x="1"
        y="3"
        width="14"
        height="10"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.4"
      />
      <path
        d="M5 7h6M5 10h3"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}
function BoxIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <path
        d="M2 5l6-3 6 3v6l-6 3-6-3V5z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <path
        d="M8 2v12M2 5l6 3 6-3"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}
