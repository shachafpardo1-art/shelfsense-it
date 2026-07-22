import os


def parse_cors_origins(value: str | None) -> list[str]:
    if not value:
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def parse_app_env(value: str | None) -> str:
    normalized = (value or "development").strip().lower()
    if normalized in {"development", "production"}:
        return normalized
    return "development"


def parse_log_format(value: str | None, default: str) -> str:
    normalized = (value or default).strip().lower()
    if normalized in {"console", "json"}:
        return normalized
    return default


def parse_log_level(value: str | None) -> str:
    normalized = (value or "INFO").strip().upper()
    if normalized in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
        return normalized
    return "INFO"


title = "ShelfSense IT API"
description = "Backend API for the ShelfSense IT inventory management platform."
version = "0.1.0"
app_env = parse_app_env(os.getenv("APP_ENV"))
log_level = parse_log_level(os.getenv("LOG_LEVEL"))
log_format = parse_log_format(
    os.getenv("LOG_FORMAT"),
    "json" if app_env == "production" else "console",
)
log_color = parse_bool(os.getenv("LOG_COLOR"), True)
cors_allow_origins = parse_cors_origins(
    os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
)
