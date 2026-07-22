import logging
import re
import time
import uuid

from fastapi import Request, Response
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Info, generate_latest

from app.config import title, version
from app.logging_config import (
    reset_request_context,
    reset_request_id,
    set_request_context,
    set_request_id,
    update_request_context,
)


logger = logging.getLogger(__name__)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
UNMATCHED_ROUTE_LABEL = "unmatched"
METRICS_PATH = "/metrics"
metrics_registry = CollectorRegistry()
http_requests_total = Counter(
    "shelfsense_http_requests_total",
    "Total HTTP requests processed by the application.",
    ["method", "route", "status_code"],
    registry=metrics_registry,
)
http_request_duration_seconds = Histogram(
    "shelfsense_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "route"],
    registry=metrics_registry,
)
http_active_requests = Gauge(
    "shelfsense_http_active_requests",
    "Number of active HTTP requests currently being processed.",
    registry=metrics_registry,
)
http_server_exceptions_total = Counter(
    "shelfsense_http_server_exceptions_total",
    "Total unhandled server exceptions raised while processing HTTP requests.",
    ["method", "route"],
    registry=metrics_registry,
)
app_info = Info(
    "shelfsense_app",
    "Application metadata.",
    registry=metrics_registry,
)
app_info.info({"service_name": title, "version": version})


def render_metrics() -> bytes:
    return generate_latest(metrics_registry)


def resolve_route_label(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None:
        path_format = getattr(route, "path_format", None)
        if path_format:
            return path_format

        path = getattr(route, "path", None)
        if path:
            return path

    return UNMATCHED_ROUTE_LABEL


def resolve_request_id(request: Request) -> str:
    request_id = request.headers.get("X-Request-ID", "").strip()
    if REQUEST_ID_PATTERN.fullmatch(request_id):
        return request_id
    return str(uuid.uuid4())


def should_track_metrics(request: Request) -> bool:
    return request.url.path != METRICS_PATH


async def request_logging_middleware(request: Request, call_next) -> Response:
    request_id = resolve_request_id(request)
    request_id_token = set_request_id(request_id)
    context_tokens = set_request_context(
        method=request.method,
        route=resolve_route_label(request),
        path=request.url.path,
    )
    start_time = time.perf_counter()
    track_metrics = should_track_metrics(request)
    if track_metrics:
        http_active_requests.inc()

    try:
        response = await call_next(request)
        duration_seconds = time.perf_counter() - start_time
        duration_ms = duration_seconds * 1000
        route_label = resolve_route_label(request)
        update_request_context(response.status_code, duration_ms, route_label)
        response.headers["X-Request-ID"] = request_id
        if track_metrics:
            http_requests_total.labels(
                method=request.method,
                route=route_label,
                status_code=str(response.status_code),
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method,
                route=route_label,
            ).observe(duration_seconds)

        log_method = logger.error if response.status_code >= 500 else logger.info
        log_method("request_completed")
        return response
    except Exception:
        duration_seconds = time.perf_counter() - start_time
        duration_ms = duration_seconds * 1000
        route_label = resolve_route_label(request)
        update_request_context(500, duration_ms, route_label)
        if track_metrics:
            http_requests_total.labels(
                method=request.method,
                route=route_label,
                status_code="500",
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method,
                route=route_label,
            ).observe(duration_seconds)
            http_server_exceptions_total.labels(
                method=request.method,
                route=route_label,
            ).inc()

        logger.exception("request_failed")
        raise
    finally:
        if track_metrics:
            http_active_requests.dec()
        reset_request_context(context_tokens)
        reset_request_id(request_id_token)
