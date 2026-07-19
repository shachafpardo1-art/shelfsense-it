from fastapi import FastAPI

from app.config import description, log_level, title, version
from app.logging_config import configure_logging
from app.routers.api import api_router
from app.routers.health import router as health_router


configure_logging(log_level)

app = FastAPI(title=title, description=description, version=version)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "ShelfSense IT API is running"}


app.include_router(health_router)
app.include_router(api_router)
