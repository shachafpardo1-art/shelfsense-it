from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.item import ItemCreate, ItemResponse
from app.services.item_service import create_item, get_active_item_by_id, list_active_items


router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item_endpoint(item_in: ItemCreate, db: Session = Depends(get_db)) -> ItemResponse:
    return create_item(db, item_in)


@router.get("", response_model=list[ItemResponse])
def list_items_endpoint(db: Session = Depends(get_db)) -> list[ItemResponse]:
    return list_active_items(db)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item_endpoint(item_id: int, db: Session = Depends(get_db)) -> ItemResponse:
    item = get_active_item_by_id(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item
