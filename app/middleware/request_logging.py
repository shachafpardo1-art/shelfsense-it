import logging
import time
import uuid

from fastapi import Request, Response

from app.logging_config import reset_request_id, set_request_id


logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next) -> Response:
    request_id = str(uuid.uuid4())
    token = set_request_id(request_id)
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed method=%s path=%s status_code=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            "request_failed method=%s path=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise
    finally:
        reset_request_id(token)
