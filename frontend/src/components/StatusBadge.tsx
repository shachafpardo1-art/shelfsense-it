import type { InventoryStatus } from "../types/api";

const labels: Record<InventoryStatus, string> = {
  in_stock: "In stock",
  low_stock: "Low stock",
  out_of_stock: "Out of stock",
};

export function StatusBadge({ status }: { status: InventoryStatus }): JSX.Element {
  return (
    <span className={`status-badge status-${status}`}>
      <span className="status-dot" aria-hidden="true" />
      {labels[status]}
    </span>
  );
}
