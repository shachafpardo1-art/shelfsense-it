import logging

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


logger = logging.getLogger("app.items")


def normalize_filter_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def create_item(db: Session, item_in: ItemCreate) -> Item:
    item = Item(**item_in.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.error(
            "😞 Item could not be created because the database reported a duplicate or integrity error operation=create_item sku=%s",
            item_in.sku,
        )
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "😞 Item could not be created because of an unexpected database failure operation=create_item sku=%s",
            item_in.sku,
        )
        raise
    db.refresh(item)
    logger.info("😊 Item created successfully operation=create_item item_id=%s sku=%s", item.id, item.sku)
    return item


def list_active_items(db: Session) -> list[Item]:
    return list_filtered_active_items(db)


def list_filtered_active_items(
    db: Session,
    search: str | None = None,
    category: str | None = None,
) -> list[Item]:
    query = db.query(Item).filter(Item.is_active.is_(True))

    normalized_search = normalize_filter_value(search)
    if normalized_search is not None:
        search_pattern = f"%{normalized_search}%"
        query = query.filter(
            or_(
                Item.name.ilike(search_pattern),
                Item.sku.ilike(search_pattern),
            )
        )

    normalized_category = normalize_filter_value(category)
    if normalized_category is not None:
        query = query.filter(func.lower(Item.category) == normalized_category.lower())

    return query.order_by(Item.id.asc()).all()


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
            "😞 Item could not be updated because the database reported a duplicate or integrity error operation=update_item item_id=%s sku=%s",
            item_id,
            item_in.sku if item_in.sku is not None else item.sku,
        )
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "😞 Item could not be updated because of an unexpected database failure operation=update_item item_id=%s sku=%s",
            item_id,
            item_in.sku if item_in.sku is not None else item.sku,
        )
        raise
    db.refresh(item)
    logger.info("😊 Item updated successfully operation=update_item item_id=%s sku=%s", item.id, item.sku)
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
            "😞 Item could not be deleted because the database reported a duplicate or integrity error operation=delete_item item_id=%s sku=%s",
            item_id,
            item.sku,
        )
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "😞 Item could not be deleted because of an unexpected database failure operation=delete_item item_id=%s sku=%s",
            item_id,
            item.sku,
        )
        raise
    db.refresh(item)
    logger.info("😊 Item deleted successfully operation=delete_item item_id=%s sku=%s", item.id, item.sku)
    return item
