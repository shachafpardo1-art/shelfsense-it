from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models.item import Item


SEED_ITEMS = [
    {
        "name": "NVIDIA GeForce RTX 5070",
        "category": "GPU",
        "sku": "GPU-RTX5070-001",
        "quantity": 24,
        "unit_price": Decimal("2799.00"),
        "reorder_level": 5,
    },
    {
        "name": "NVIDIA GeForce RTX 4090",
        "category": "GPU",
        "sku": "GPU-RTX4090-001",
        "quantity": 2,
        "unit_price": Decimal("8999.00"),
        "reorder_level": 3,
    },
    {
        "name": "Samsung 990 Pro 2TB SSD",
        "category": "SSD",
        "sku": "SSD-990PRO-2TB",
        "quantity": 18,
        "unit_price": Decimal("749.00"),
        "reorder_level": 6,
    },
    {
        "name": "Kingston Fury DDR5 32GB",
        "category": "RAM",
        "sku": "RAM-KF-DDR5-32",
        "quantity": 8,
        "unit_price": Decimal("429.00"),
        "reorder_level": 5,
    },
    {
        "name": "Cisco CBS250 Network Switch",
        "category": "Network Switch",
        "sku": "NET-CBS250-001",
        "quantity": 5,
        "unit_price": Decimal("1499.00"),
        "reorder_level": 5,
    },
    {
        "name": "TP-Link Archer AX73 Router",
        "category": "Router",
        "sku": "NET-AX73-001",
        "quantity": 0,
        "unit_price": Decimal("699.00"),
        "reorder_level": 4,
    },
]


def main() -> None:
    db = SessionLocal()
    inserted = 0
    skipped = 0

    try:
        for item_data in SEED_ITEMS:
            existing_item = db.query(Item).filter(Item.sku == item_data["sku"]).first()
            if existing_item is not None:
                skipped += 1
                continue

            db.add(Item(**item_data))
            inserted += 1

        db.commit()
        print(f"Seed complete inserted={inserted} skipped={skipped}")
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
