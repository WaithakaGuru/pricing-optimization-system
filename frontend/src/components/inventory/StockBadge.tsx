import type { StockStatus } from '../../types';

const CONFIG: Record<StockStatus, { label: string; classes: string; dot: string }> = {
  ok:        { label: 'In Stock',  classes: 'bg-[--color-success-light] text-[--color-success]', dot: 'bg-[--color-success]' },
  low:       { label: 'Low Stock', classes: 'bg-[--color-warning-light] text-[--color-warning]', dot: 'bg-[--color-warning]' },
  critical:  { label: 'Critical',  classes: 'bg-[--color-danger-light]  text-[--color-danger]',  dot: 'bg-[--color-danger]'  },
  overstock: { label: 'Overstock', classes: 'bg-[--color-accent-light]  text-[--color-accent]',  dot: 'bg-[--color-accent]'  },
};

export function getStockStatus(qty: number, reorder: number): StockStatus {
  if (qty <= reorder * 0.5) return 'critical';
  if (qty <= reorder)       return 'low';
  if (qty >= reorder * 6)   return 'overstock';
  return 'ok';
}

export default function StockBadge({ status }: { status: StockStatus }) {
  const { label, classes, dot } = CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full ${classes}`}>
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dot}`} />
      {label}
    </span>
  );
}
