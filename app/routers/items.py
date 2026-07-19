import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.item_service import (
    create_item,
    deactivate_item,
    get_active_item_by_id,
    item_exists_by_sku,
    list_filtered_active_items,
    update_active_item,
)


logger = logging.getLogger("app.items")

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item_endpoint(item_in: ItemCreate, db: Session = Depends(get_db)) -> ItemResponse:
    if item_exists_by_sku(db, item_in.sku):
        logger.warning("Duplicate SKU attempt operation=create_item sku=%s", item_in.sku)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    try:
        return create_item(db, item_in)
    except IntegrityError as exc:
        logger.warning("Duplicate SKU attempt operation=create_item sku=%s", item_in.sku)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists") from exc


@router.get("", response_model=list[ItemResponse])
def list_items_endpoint(
    search: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
) -> list[ItemResponse]:
    return list_filtered_active_items(db, search=search, category=category)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item_endpoint(item_id: int, db: Session = Depends(get_db)) -> ItemResponse:
    item = get_active_item_by_id(db, item_id)
    if item is None:
        logger.warning("Item not found operation=get_item item_id=%s", item_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item_endpoint(
    item_id: int,
    item_in: ItemUpdate,
    db: Session = Depends(get_db),
) -> ItemResponse:
    existing_item = get_active_item_by_id(db, item_id)
    if existing_item is None:
        logger.warning("Item not found operation=update_item item_id=%s", item_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if item_in.sku is not None and item_exists_by_sku(db, item_in.sku, exclude_item_id=item_id):
        logger.warning("Duplicate SKU attempt operation=update_item item_id=%s sku=%s", item_id, item_in.sku)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    try:
        updated_item = update_active_item(db, item_id, item_in)
    except IntegrityError as exc:
        logger.warning("Duplicate SKU attempt operation=update_item item_id=%s sku=%s", item_id, item_in.sku)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists") from exc

    if updated_item is None:
        logger.warning("Item not found operation=update_item item_id=%s", item_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_endpoint(item_id: int, db: Session = Depends(get_db)) -> Response:
    item = deactivate_item(db, item_id)
    if item is None:
        logger.warning("Item not found operation=delete_item item_id=%s", item_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
