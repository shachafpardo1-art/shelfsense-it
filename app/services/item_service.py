from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate


def create_item(db: Session, item_in: ItemCreate) -> Item:
    item = Item(**item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_active_items(db: Session) -> list[Item]:
    return db.query(Item).filter(Item.is_active.is_(True)).all()


def get_active_item_by_id(db: Session, item_id: int) -> Item | None:
    return (
        db.query(Item)
        .filter(Item.id == item_id, Item.is_active.is_(True))
        .first()
    )
