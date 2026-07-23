import logging
import json
import sys
from contextvars import ContextVar, Token
from datetime import datetime, timezone


RESET_COLOR = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
request_method_context: ContextVar[str] = ContextVar("request_method", default="-")
request_route_context: ContextVar[str] = ContextVar("request_route", default="-")
request_path_context: ContextVar[str] = ContextVar("request_path", default="-")
status_code_context: ContextVar[str] = ContextVar("status_code", default="-")
duration_ms_context: ContextVar[str] = ContextVar("duration_ms", default="-")


def set_request_id(request_id: str) -> Token[str]:
    return request_id_context.set(request_id)


def get_request_id() -> str:
    return request_id_context.get()


def reset_request_id(token: Token[str]) -> None:
    request_id_context.reset(token)


def set_request_context(
    method: str,
    route: str,
    path: str,
    status_code: str = "-",
    duration_ms: str = "-",
) -> dict[str, Token[str]]:
    return {
        "method": request_method_context.set(method),
        "route": request_route_context.set(route),
        "path": request_path_context.set(path),
        "status_code": status_code_context.set(status_code),
        "duration_ms": duration_ms_context.set(duration_ms),
    }


def update_request_context(status_code: int, duration_ms: float, route: str) -> None:
    request_route_context.set(route)
    status_code_context.set(str(status_code))
    duration_ms_context.set(f"{duration_ms:.2f}")


def reset_request_context(tokens: dict[str, Token[str]]) -> None:
    request_method_context.reset(tokens["method"])
    request_route_context.reset(tokens["route"])
    request_path_context.reset(tokens["path"])
    status_code_context.reset(tokens["status_code"])
    duration_ms_context.reset(tokens["duration_ms"])


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", get_request_id())
        record.method = getattr(record, "method", request_method_context.get())
        record.route = getattr(record, "route", request_route_context.get())
        record.path = getattr(record, "path", request_path_context.get())
        record.status_code = getattr(record, "status_code", status_code_context.get())
        record.duration_ms = getattr(record, "duration_ms", duration_ms_context.get())
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": record.request_id,
            "method": record.method,
            "route": record.route,
            "path": record.path,
            "status_code": record.status_code,
            "duration_ms": record.duration_ms,
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


class ConsoleLogFormatter(logging.Formatter):
    def __init__(self, use_color: bool) -> None:
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        message = (
            f"{timestamp} {record.levelname} method={record.method} route={record.route} "
            f"path={record.path} status_code={record.status_code} duration_ms={record.duration_ms} "
            f"request_id={record.request_id} message={record.getMessage()}"
        )

        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"

        if not self.use_color:
            return message

        color = self._select_color(record)
        if not color:
            return message
        return f"{color}{message}{RESET_COLOR}"

    def _select_color(self, record: logging.LogRecord) -> str:
        if record.exc_info or record.levelno >= logging.ERROR:
            return RED

        try:
            status_code = int(record.status_code)
        except (TypeError, ValueError):
            return ""

        if 200 <= status_code < 300:
            return GREEN
        if 300 <= status_code < 500:
            return YELLOW
        if status_code >= 500:
            return RED
        return ""


def configure_logging(log_level: str, log_format: str = "console", log_color: bool = True) -> None:
    root_logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestContextFilter())

    use_color = (
        log_format == "console"
        and log_color
        and hasattr(sys.stdout, "isatty")
        and sys.stdout.isatty()
    )
    if log_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(ConsoleLogFormatter(use_color=use_color))

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.propagate = False

    configure_logging._configured = True
