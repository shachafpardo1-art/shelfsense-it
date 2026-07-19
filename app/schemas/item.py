from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ItemCreate(BaseModel):
    name: str
    category: str
    sku: str
    quantity: int
    unit_price: Decimal


class ItemResponse(BaseModel):
    id: int
    name: str
    category: str
    sku: str
    quantity: int
    unit_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
