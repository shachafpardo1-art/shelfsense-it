import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


logger = logging.getLogger("app.items")


def create_item(db: Session, item_in: ItemCreate) -> Item:
    item = Item(**item_in.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.error(
            "Database IntegrityError operation=create_item sku=%s",
            item_in.sku,
        )
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "Unexpected database commit failure operation=create_item sku=%s",
            item_in.sku,
        )
        raise
    db.refresh(item)
    logger.info("Item created operation=create_item item_id=%s sku=%s", item.id, item.sku)
    return item


def list_active_items(db: Session) -> list[Item]:
    return db.query(Item).filter(Item.is_active.is_(True)).all()


def get_active_item_by_id(db: Session, item_id: int) -> Item | None:
    return (
        db.query(Item)
        .filter(Item.id == item_id, Item.is_active.is_(True))
        .first()
    )


def item_exists_by_sku(db: Session, sku: str, exclude_item_id: int | None = None) -> bool:
    query = db.query(Item).filter(Item.sku == sku)
    if exclude_item_id is not None:
        query = query.filter(Item.id != exclude_item_id)
    return db.query(query.exists()).scalar()


def update_active_item(db: Session, item_id: int, item_in: ItemUpdate) -> Item | None:
    item = get_active_item_by_id(db, item_id)
    if item is None:
        return None

    for field, value in item_in.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.error(
            "Database IntegrityError operation=update_item item_id=%s sku=%s",
            item_id,
            item_in.sku if item_in.sku is not None else item.sku,
        )
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "Unexpected database commit failure operation=update_item item_id=%s sku=%s",
            item_id,
            item_in.sku if item_in.sku is not None else item.sku,
        )
        raise
    db.refresh(item)
    logger.info("Item updated operation=update_item item_id=%s sku=%s", item.id, item.sku)
    return item


def deactivate_item(db: Session, item_id: int) -> Item | None:
    item = get_active_item_by_id(db, item_id)
    if item is None:
        return None

    item.is_active = False
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.error(
            "Database IntegrityError operation=delete_item item_id=%s sku=%s",
            item_id,
            item.sku,
        )
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "Unexpected database commit failure operation=delete_item item_id=%s sku=%s",
            item_id,
            item.sku,
        )
        raise
    db.refresh(item)
    logger.info("Item soft deleted operation=delete_item item_id=%s sku=%s", item.id, item.sku)
    return item
