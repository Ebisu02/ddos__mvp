"""
Very small HTTP server (no external libs).

Routes:
- /            dashboard (HTML)
- /api/metrics  JSON metrics
- /api/incidents JSON incidents
- /api/analysis JSON analysis rows joined with metrics
- /api/top-sources JSON top sources (real, from DB)
- /health      ok
"""
from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from typing import Callable, Any

from storage.database import fetch_metrics, fetch_incidents, fetch_analysis, fetch_top_sources


def _json(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _html(handler: BaseHTTPRequestHandler, html: str, status: int = 200) -> None:
    body = html.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def make_handler(db_path: str, render_dashboard: Callable[[str, str, str, str], str]):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/health":
                return _json(self, {"status": "ok", "ts": int(time.time())})

            if path == "/api/metrics":
                qs = parse_qs(parsed.query)
                limit = int(qs.get("limit", ["200"])[0])
                return _json(self, fetch_metrics(db_path, since_ts=None, limit=limit))

            if path == "/api/incidents":
                qs = parse_qs(parsed.query)
                limit = int(qs.get("limit", ["50"])[0])
                return _json(self, fetch_incidents(db_path, limit=limit))

            if path == "/api/analysis":
                qs = parse_qs(parsed.query)
                limit = int(qs.get("limit", ["200"])[0])
                return _json(self, fetch_analysis(db_path, limit=limit))

            if path == "/api/top-sources":
                qs = parse_qs(parsed.query)
                limit = int(qs.get("limit", ["5"])[0])
                window = int(qs.get("window", ["3600"])[0])
                return _json(self, fetch_top_sources(db_path, limit=limit, window_seconds=window))

            if path == "/":
                html = render_dashboard(
                    "/api/metrics?limit=240",
                    "/api/incidents?limit=80",
                    "/api/analysis?limit=240",
                    "/api/top-sources?limit=5&window=3600",
                )
                return _html(self, html)

            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            return

    return Handler


def serve(host: str, port: int, db_path: str, render_dashboard: Callable[[str, str, str, str], str]) -> None:
    handler_cls = make_handler(db_path, render_dashboard)
    httpd = HTTPServer((host, port), handler_cls)
    print(f"[web] http://{host}:{port}/")
    httpd.serve_forever()
