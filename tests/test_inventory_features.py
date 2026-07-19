import unittest
from datetime import datetime
from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.dashboard_service import get_dashboard_summary
from app.services.item_service import list_filtered_active_items


class InventoryFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_item_create_normalizes_text_and_defaults_reorder_level(self) -> None:
        item = ItemCreate(
            name="  NVIDIA GeForce RTX 5070  ",
            category="  GPU  ",
            sku="  GPU-RTX5070-001  ",
            quantity=24,
            unit_price=Decimal("2799.00"),
        )

        self.assertEqual(item.name, "NVIDIA GeForce RTX 5070")
        self.assertEqual(item.category, "GPU")
        self.assertEqual(item.sku, "GPU-RTX5070-001")
        self.assertEqual(item.reorder_level, 5)

    def test_item_update_rejects_whitespace_only_text(self) -> None:
        with self.assertRaises(ValidationError):
            ItemUpdate(name="   ")

    def test_item_response_status_is_computed(self) -> None:
        base_payload = {
            "id": 1,
            "name": "Test Item",
            "category": "GPU",
            "sku": "TEST-001",
            "reorder_level": 5,
            "unit_price": Decimal("10.00"),
            "is_active": True,
            "created_at": datetime(2026, 7, 19, 12, 0, 0),
            "updated_at": datetime(2026, 7, 19, 12, 0, 0),
        }

        self.assertEqual(ItemResponse(**base_payload, quantity=0).status, "out_of_stock")
        self.assertEqual(ItemResponse(**base_payload, quantity=5).status, "low_stock")
        self.assertEqual(ItemResponse(**base_payload, quantity=6).status, "in_stock")

    def test_list_filters_and_dashboard_summary_ignore_inactive_items(self) -> None:
        db = self.session_factory()
        try:
            db.add_all(
                [
                    Item(
                        name="NVIDIA GeForce RTX 5070",
                        category="GPU",
                        sku="GPU-RTX5070-001",
                        quantity=24,
                        reorder_level=5,
                        unit_price=Decimal("2799.00"),
                        is_active=True,
                    ),
                    Item(
                        name="NVIDIA GeForce RTX 4090",
                        category="GPU",
                        sku="GPU-RTX4090-001",
                        quantity=2,
                        reorder_level=3,
                        unit_price=Decimal("8999.00"),
                        is_active=True,
                    ),
                    Item(
                        name="TP-Link Archer AX73 Router",
                        category="Router",
                        sku="NET-AX73-001",
                        quantity=0,
                        reorder_level=4,
                        unit_price=Decimal("699.00"),
                        is_active=True,
                    ),
                    Item(
                        name="Retired GPU",
                        category="GPU",
                        sku="GPU-OLD-001",
                        quantity=100,
                        reorder_level=5,
                        unit_price=Decimal("99.00"),
                        is_active=False,
                    ),
                ]
            )
            db.commit()

            filtered_items = list_filtered_active_items(db, search="rtx", category="gpu")
            self.assertEqual([item.sku for item in filtered_items], ["GPU-RTX5070-001", "GPU-RTX4090-001"])

            summary = get_dashboard_summary(db)
            self.assertEqual(summary.total_products, 3)
            self.assertEqual(summary.total_units, 26)
            self.assertEqual(summary.total_inventory_value, Decimal("85174.00"))
            self.assertEqual(summary.low_stock_count, 1)
            self.assertEqual(summary.out_of_stock_count, 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
