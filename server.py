"""Local HTTP server for testing the decision engine."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from main import run_decision_engine


class DecisionEngineHandler(BaseHTTPRequestHandler):
    server_version = "OpenApplyv2LocalServer/1.0"

    def _write_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._write_json(200, {"status": "ok"})
            return
        self._write_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/evaluate":
            self._write_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a JSON object")
        except Exception as exc:
            self._write_json(400, {"error": f"Invalid JSON payload: {exc}"})
            return

        try:
            result = run_decision_engine(payload)
            self._write_json(200, result)
        except Exception as exc:
            self._write_json(500, {"error": f"Internal error: {exc}"})


def run_local_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), DecisionEngineHandler)
    print(f"Server running on http://{host}:{port}")
    print("POST /evaluate and GET /health are available.")
    server.serve_forever()


if __name__ == "__main__":
    run_local_server()
