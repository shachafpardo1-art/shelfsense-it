from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_allow_origins, description, log_level, title, version
from app.logging_config import configure_logging
from app.routers.api import api_router
from app.routers.health import router as health_router


configure_logging(log_level)

app = FastAPI(title=title, description=description, version=version)

if cors_allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "ShelfSense IT API is running"}


app.include_router(health_router)
app.include_router(api_router)
