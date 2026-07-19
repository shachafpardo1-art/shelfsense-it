import os


def parse_cors_origins(value: str | None) -> list[str]:
    if not value:
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]


title = "ShelfSense IT API"
description = "Backend API for the ShelfSense IT inventory management platform."
version = "0.1.0"
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
cors_allow_origins = parse_cors_origins(
    os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
)
