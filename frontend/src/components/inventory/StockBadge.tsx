import type { StockStatus } from "../../types";

const CONFIG: Record<
  StockStatus,
  { label: string; classes: string; dot: string }
> = {
  ok: {
    label: "In Stock",
    classes: "bg-success-light text-success",
    dot: "bg-success]",
  },
  low: {
    label: "Low Stock",
    classes: "bg-warning-light text-warning",
    dot: "bg-warning]",
  },
  critical: {
    label: "Critical",
    classes: "bg-danger-light text-danger",
    dot: "bg-danger",
  },
  overstock: {
    label: "Overstock",
    classes: "bg-accent-light text-accent",
    dot: "bg-accent",
  },
};

export function getStockStatus(qty: number, reorder: number): StockStatus {
  if (qty <= reorder * 0.5) return "critical";
  if (qty <= reorder) return "low";
  if (qty >= reorder * 6) return "overstock";
  return "ok";
}

export default function StockBadge({ status }: { status: StockStatus }) {
  const { label, classes, dot } = CONFIG[status];
  return (
    <span
      className={`inline-flex items-center text-xs font-medium px-1.5 py-1 rounded-full ${classes} mr-6`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dot}`} />
      {label}
    </span>
  );
}
