export type InventoryStatus = "in_stock" | "low_stock" | "out_of_stock";

export interface DashboardSummary {
  total_products: number;
  total_units: number;
  total_inventory_value: number | string;
  low_stock_count: number;
  out_of_stock_count: number;
}

export interface Item {
  id: number;
  name: string;
  category: string;
  sku: string;
  quantity: number;
  reorder_level: number;
  unit_price: number | string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  status: InventoryStatus;
}

export interface ItemCreateInput {
  name: string;
  category: string;
  sku: string;
  quantity: number;
  reorder_level: number;
  unit_price: string;
}

export interface ItemUpdateInput {
  name?: string;
  category?: string;
  sku?: string;
  quantity?: number;
  reorder_level?: number;
  unit_price?: string;
}
