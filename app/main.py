from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST

from app.config import (
    cors_allow_origins,
    description,
    log_color,
    log_format,
    log_level,
    title,
    version,
)
from app.logging_config import configure_logging
from app.middleware import request_logging_middleware
from app.middleware.request_logging import render_metrics
from app.routers.api import api_router
from app.routers.health import router as health_router


configure_logging(log_level, log_format=log_format, log_color=log_color)

app = FastAPI(title=title, description=description, version=version)
app.middleware("http")(request_logging_middleware)

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


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=render_metrics(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(api_router)
