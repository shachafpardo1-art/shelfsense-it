from decimal import Decimal

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_products: int
    total_units: int
    total_inventory_value: Decimal
    low_stock_count: int
    out_of_stock_count: int
