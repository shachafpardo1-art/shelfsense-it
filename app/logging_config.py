import logging
import sys
from contextvars import ContextVar, Token


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def set_request_id(request_id: str) -> Token[str]:
    return request_id_context.set(request_id)


def get_request_id() -> str:
    return request_id_context.get()


def reset_request_id(token: Token[str]) -> None:
    request_id_context.reset(token)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_logging(log_level: str) -> None:
    root_logger = logging.getLogger()

    if getattr(configure_logging, "_configured", False):
        root_logger.setLevel(log_level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    configure_logging._configured = True
