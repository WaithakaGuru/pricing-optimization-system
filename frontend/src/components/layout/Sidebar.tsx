import { NavLink } from "react-router-dom";
import { X } from "lucide-react";
import { useSidebar } from "../../contexts/SidebarContext";

const NAV = [
  {
    group: "OVERVIEW",
    items: [{ to: "/", icon: <GridIcon />, label: "Dashboard" }],
  },
  {
    group: "PRICING",
    items: [{ to: "/prices", icon: <TagIcon />, label: "Optimize Price" }],
  },
  {
    group: "OPERATIONS",
    items: [
      { to: "/pos", icon: <PosIcon />, label: "POS Terminal" },
      { to: "/inventory", icon: <BoxIcon />, label: "Inventory" },
    ],
  },
  {
    group: "ANALYSIS",
    items: [
      { to: "/agents", icon: <BrainIcon />, label: "Agent Training" },
      { to: "/models", icon: <ChartIcon />, label: "Model Comparison" },
    ],
  },
];

export default function Sidebar() {
  const { isOpen, closeSidebar } = useSidebar();

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 md:hidden z-30"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:sticky top-16 md:top-0 left-0 h-[calc(100vh-64px)] md:h-screen w-58 bg-surface border-r border-border flex flex-col z-40 transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{ width: "232px" }}
      >
        {/* Mobile close button */}
        <button
          onClick={closeSidebar}
          className="md:hidden flex items-center justify-between px-5 py-4 border-b border-border hover:bg-surface-2 transition-colors"
          aria-label="Close navigation"
        >
          <span className="text-sm font-semibold tracking-widest text-text-primary uppercase">Menu</span>
          <X className="w-5 h-5 text-text-primary" />
        </button>

        {/* Logo - hidden on mobile since TopBar has menu */}
        <div className="hidden md:flex items-center gap-2.5 px-5 py-5 border-b border-border">
          <div className="w-8 h-8 rounded-lg bg-accent text-white flex items-center justify-center text-sm font-bold tracking-tight shrink-0">
            O
          </div>
          <span className="text-sm font-semibold tracking-widest text-text-primary">
            OPTIMA
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 flex flex-col gap-6 overflow-y-auto">
          {NAV.map((group) => (
            <div key={group.group} className="flex flex-col gap-0.5">
              <span className="text-[10px] font-semibold tracking-widest text-text-primary px-2 pb-1.5 uppercase">
                {group.group}
              </span>
              {group.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  onClick={closeSidebar}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-2.5 py-2 rounded-md text-[13.5px] font-medium transition-colors duration-100 ${
                      isActive
                        ? "bg-accent-light text-accent"
                        : "text-text-secondary hover:bg-surface-2 hover:text-text-primary"
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
        <div className="flex items-center gap-2 px-5 py-3.5 border-t border-border">
          <div className="w-1.5 h-1.5 rounded-full bg-border-2 shrink-0" />
          <span className="text-xs text-text-tertiary">Backend offline</span>
        </div>
      </aside>
    </>
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

function TagIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <path
        d="M2 8l6-6h6v6l-6 6H2V8z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <circle cx="11" cy="5" r="1" fill="currentColor" />
    </svg>
  );
}

function BrainIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <path
        d="M3 10c-1 0-1.5-1-1.5-2.5S2 5 3 5c1 0 1 1 1 2.5S4 10 3 10m10 0c1 0 1.5-1 1.5-2.5S14 5 13 5c-1 0-1 1-1 2.5S12 10 13 10m-5-7c-2 0-3 1-3 3s1 3 3 3 3-1 3-3-1-3-3-3"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <path
        d="M2 14h12M2 11l3-3 3 2 4-5M12 4v5"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
