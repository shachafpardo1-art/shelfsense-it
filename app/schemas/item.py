from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


InventoryStatus = Literal["out_of_stock", "low_stock", "in_stock"]


def normalize_text_field(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    normalized = value.strip()
    if not normalized:
        raise ValueError("must not be empty")
    return normalized


class ItemCreate(BaseModel):
    name: str
    category: str
    sku: str
    quantity: int = Field(ge=0)
    reorder_level: int = Field(default=5, ge=0)
    unit_price: Decimal = Field(ge=0)

    _normalize_name = field_validator("name", mode="before")(normalize_text_field)
    _normalize_category = field_validator("category", mode="before")(normalize_text_field)
    _normalize_sku = field_validator("sku", mode="before")(normalize_text_field)


class ItemUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    sku: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)

    _normalize_name = field_validator("name", mode="before")(normalize_text_field)
    _normalize_category = field_validator("category", mode="before")(normalize_text_field)
    _normalize_sku = field_validator("sku", mode="before")(normalize_text_field)


class ItemResponse(BaseModel):
    id: int
    name: str
    category: str
    sku: str
    quantity: int
    reorder_level: int
    unit_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field(return_type=str)
    @property
    def status(self) -> InventoryStatus:
        if self.quantity == 0:
            return "out_of_stock"
        if self.quantity <= self.reorder_level:
            return "low_stock"
        return "in_stock"
