from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote

from .model import OperationalSignal
from .store import HealthStore

COMPONENT = "goreecloud-observability"
VERSION = "0.1.0-dev"
STORE = HealthStore()


def health_payload() -> dict[str, Any]:
    return {"status": "healthy", "component": COMPONENT, "version": VERSION, "scope": "development-reference-runtime"}


def readiness_payload() -> dict[str, Any]:
    return {"status": "ready", "component": COMPONENT, "version": VERSION, "production_accepted": False}


class Handler(BaseHTTPRequestHandler):
    server_version = "GoreeCloudObservability/0.1"

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._json(200, health_payload())
            return
        if self.path == "/readyz":
            self._json(200, readiness_payload())
            return
        prefix = "/v1/components/"
        suffix = "/health"
        if self.path.startswith(prefix) and self.path.endswith(suffix):
            component_id = unquote(self.path[len(prefix):-len(suffix)]).strip("/")
            if not component_id:
                self._json(400, {"error": "invalid_component"})
                return
            self._json(200, STORE.health(component_id))
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/signals":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 262144:
                raise ValueError("request body size is invalid")
            payload = json.loads(self.rfile.read(length))
            signal = OperationalSignal.from_mapping(payload)
            STORE.add(signal)
            self._json(202, {"accepted": True, "signal_id": signal.signal_id, "component_id": signal.component_id})
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"accepted": False, "error": "invalid_signal", "message": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        # Avoid request-body and attribute logging in the Development reference runtime.
        return


def serve() -> None:
    host = os.environ.get("GOREECLOUD_OBSERVABILITY_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Development runtime refuses non-loopback binding")
    port = int(os.environ.get("GOREECLOUD_OBSERVABILITY_PORT", "8790"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
