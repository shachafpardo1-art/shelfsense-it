import asyncio
import io
import json
import socket
import subprocess
import sys
import time
import unittest
import urllib.request
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.logging_config import configure_logging
from app.main import app
from app.middleware.request_logging import (
    http_active_requests,
    http_requests_total,
    request_logging_middleware,
)


class CaptureStream(io.StringIO):
    def __init__(self, is_tty: bool) -> None:
        super().__init__()
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def http_get(base_url: str, path: str) -> tuple[int, dict[str, str], bytes]:
    with urllib.request.urlopen(f"{base_url}{path}", timeout=5) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        return response.status, headers, response.read()


def build_request(
    path: str,
    route_path: str | None = None,
    headers: dict[str, str] | None = None,
    query_string: bytes = b"",
) -> Request:
    encoded_headers = []
    for key, value in (headers or {}).items():
        encoded_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": query_string,
        "headers": encoded_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    if route_path is not None:
        scope["route"] = SimpleNamespace(path=route_path, path_format=route_path)

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive)


def run_middleware(request: Request, call_next) -> Response:
    return asyncio.run(request_logging_middleware(request, call_next))


def counter_value(method: str, route: str, status_code: str) -> float:
    return http_requests_total.labels(
        method=method,
        route=route,
        status_code=status_code,
    )._value.get()


class ObservabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.port = find_free_port()
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server = subprocess.Popen(
            [
                ".venv/bin/python",
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(cls.port),
                "--log-level",
                "warning",
            ],
            cwd="/home/shachaf/shelfsense-it",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.time() + 10
        while time.time() < deadline:
            if cls.server.poll() is not None:
                raise RuntimeError("Uvicorn exited before observability tests could connect.")
            try:
                status_code, _, _ = http_get(cls.base_url, "/health")
            except Exception:
                time.sleep(0.1)
                continue
            if status_code == 200:
                return

        cls.server.terminate()
        cls.server.wait(timeout=5)
        raise RuntimeError("Timed out waiting for uvicorn test server to start.")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.terminate()
        cls.server.wait(timeout=5)

    def test_health_endpoint_returns_expected_response(self) -> None:
        status_code, headers, body = http_get(self.base_url, "/health")

        self.assertEqual(status_code, 200)
        self.assertEqual(json.loads(body), {"status": "healthy"})
        self.assertEqual(headers["content-type"], "application/json")

    def test_ready_endpoint_returns_expected_response(self) -> None:
        status_code, headers, body = http_get(self.base_url, "/ready")

        self.assertEqual(status_code, 200)
        self.assertEqual(json.loads(body), {"status": "ready"})
        self.assertEqual(headers["content-type"], "application/json")

    def test_metrics_endpoint_returns_prometheus_content(self) -> None:
        status_code, headers, body = http_get(self.base_url, "/metrics")

        self.assertEqual(status_code, 200)
        self.assertIn(CONTENT_TYPE_LATEST, headers["content-type"])
        self.assertIn(b"shelfsense_http_requests_total", body)
        self.assertIn(b"shelfsense_app_info", body)

    def test_normal_request_increments_request_counter(self) -> None:
        before = counter_value("GET", "/ok", "200")
        request = build_request("/ok", route_path="/ok")

        async def call_next(_: Request) -> Response:
            return JSONResponse({"status": "ok"}, status_code=200)

        response = run_middleware(request, call_next)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(counter_value("GET", "/ok", "200") - before, 1.0)

    def test_metrics_requests_do_not_increment_http_request_counter(self) -> None:
        before = sum(metric._value.get() for metric in http_requests_total._metrics.values())
        request = build_request("/metrics", route_path="/metrics")

        async def call_next(_: Request) -> Response:
            return Response(content=b"metrics", media_type=CONTENT_TYPE_LATEST)

        response = run_middleware(request, call_next)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sum(metric._value.get() for metric in http_requests_total._metrics.values()), before)

    def test_dynamic_item_ids_share_one_normalized_route_label(self) -> None:
        before = counter_value("GET", "/api/v1/items/{item_id}", "200")

        async def call_next(_: Request) -> Response:
            return JSONResponse({"item_id": 1}, status_code=200)

        first = run_middleware(build_request("/api/v1/items/1", route_path="/api/v1/items/{item_id}"), call_next)
        second = run_middleware(build_request("/api/v1/items/2", route_path="/api/v1/items/{item_id}"), call_next)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(counter_value("GET", "/api/v1/items/{item_id}", "200") - before, 2.0)

    def test_active_request_gauge_returns_to_original_value_after_success_and_exception(self) -> None:
        before = http_active_requests._value.get()
        success_request = build_request("/ok", route_path="/ok")
        error_request = build_request("/boom", route_path="/boom")

        async def ok(_: Request) -> Response:
            return JSONResponse({"status": "ok"}, status_code=200)

        async def boom(_: Request) -> Response:
            raise RuntimeError("kaboom")

        success_response = run_middleware(success_request, ok)
        with self.assertRaises(RuntimeError):
            run_middleware(error_request, boom)

        self.assertEqual(success_response.status_code, 200)
        self.assertEqual(http_active_requests._value.get(), before)

    def test_x_request_id_is_preserved_when_valid_and_generated_when_invalid(self) -> None:
        async def ok(_: Request) -> Response:
            return JSONResponse({"status": "ok"}, status_code=200)

        preserved = run_middleware(
            build_request("/ok", route_path="/ok", headers={"X-Request-ID": "request-123"}),
            ok,
        )
        generated = run_middleware(
            build_request("/ok", route_path="/ok", headers={"X-Request-ID": "bad value with spaces"}),
            ok,
        )

        self.assertEqual(preserved.headers["X-Request-ID"], "request-123")
        self.assertIn("X-Request-ID", generated.headers)
        self.assertNotEqual(generated.headers["X-Request-ID"], "bad value with spaces")
        self.assertTrue(generated.headers["X-Request-ID"])

    def test_json_logging_contains_required_fields_without_ansi_codes(self) -> None:
        stream = CaptureStream(is_tty=False)
        request = build_request("/ok", route_path="/ok", headers={"X-Request-ID": "json-123"})

        async def ok(_: Request) -> Response:
            return JSONResponse({"status": "ok"}, status_code=200)

        with patch.object(sys, "stdout", stream):
            configure_logging("INFO", log_format="json", log_color=True)
            response = run_middleware(request, ok)

        self.assertEqual(response.status_code, 200)
        log_lines = [line for line in stream.getvalue().splitlines() if line.strip()]
        payload = json.loads(log_lines[-1])
        self.assertEqual(payload["severity"], "INFO")
        self.assertEqual(payload["method"], "GET")
        self.assertEqual(payload["route"], "/ok")
        self.assertEqual(payload["path"], "/ok")
        self.assertEqual(payload["status_code"], "200")
        self.assertEqual(payload["request_id"], "json-123")
        self.assertIn("duration_ms", payload)
        self.assertNotIn("\x1b[", log_lines[-1])

    def test_console_color_is_only_used_when_enabled_with_a_tty(self) -> None:
        request = build_request("/ok", route_path="/ok")

        async def ok(_: Request) -> Response:
            return JSONResponse({"status": "ok"}, status_code=200)

        color_stream = CaptureStream(is_tty=True)
        with patch.object(sys, "stdout", color_stream):
            configure_logging("INFO", log_format="console", log_color=True)
            run_middleware(request, ok)

        plain_stream = CaptureStream(is_tty=False)
        with patch.object(sys, "stdout", plain_stream):
            configure_logging("INFO", log_format="console", log_color=True)
            run_middleware(build_request("/ok", route_path="/ok"), ok)

        self.assertIn("\x1b[32m", color_stream.getvalue())
        self.assertNotIn("\x1b[", plain_stream.getvalue())

    def test_sensitive_values_are_not_written_to_logs(self) -> None:
        stream = CaptureStream(is_tty=False)
        request = build_request(
            "/sensitive/42",
            route_path="/sensitive/{item_id}",
            headers={
                "Authorization": "Bearer top-secret-token",
                "Cookie": "sessionid=private-cookie",
            },
            query_string=b"password=hunter2&token=shh",
        )

        async def ok(_: Request) -> Response:
            return JSONResponse({"status": "ok"}, status_code=200)

        with patch.object(sys, "stdout", stream):
            configure_logging("INFO", log_format="json", log_color=False)
            response = run_middleware(request, ok)

        self.assertEqual(response.status_code, 200)
        output = stream.getvalue()
        self.assertNotIn("hunter2", output)
        self.assertNotIn("token=shh", output)
        self.assertNotIn("top-secret-token", output)
        self.assertNotIn("private-cookie", output)
        self.assertNotIn("password=", output)


if __name__ == "__main__":
    unittest.main()
