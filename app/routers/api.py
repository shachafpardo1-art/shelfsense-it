from fastapi import APIRouter

from app.routers.dashboard import router as dashboard_router
from app.routers.items import router as items_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(dashboard_router)
api_router.include_router(items_router)
