#!/usr/bin/env python3
"""Web application wrapper for the read-only SEO/GEO audit engine."""

from __future__ import annotations

from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading
from typing import Any
from urllib.parse import urlsplit


ROOT_DIR = Path(__file__).resolve().parent
ENGINE_DIR = ROOT_DIR / "scripts"
WEB_DIR = ROOT_DIR / "web"
MAX_BODY_BYTES = 16_384
MAX_WEB_PAGES = 300
DEFAULT_WEB_PAGES = 25
AUDIT_GATE = threading.BoundedSemaphore(value=1)

sys.path.insert(0, str(ENGINE_DIR))
from site_audit import audit_site, markdown_report  # noqa: E402


class AuditRequestError(ValueError):
    """Raised when a browser request cannot be safely audited."""


def parse_audit_request(payload: Any) -> tuple[str, int]:
    """Validate browser input without exposing the local-network override."""
    if not isinstance(payload, dict):
        raise AuditRequestError("请求体必须是 JSON 对象。")

    raw_url = payload.get("url")
    if not isinstance(raw_url, str) or not raw_url.strip():
        raise AuditRequestError("请输入要巡检的公开站点 URL。")

    url = raw_url.strip()
    if "://" not in url:
        url = f"https://{url}"

    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise AuditRequestError("仅支持完整的 http:// 或 https:// 公网站点地址。")
    if parsed.username or parsed.password:
        raise AuditRequestError("URL 不能包含用户名或密码。")

    raw_max_pages = payload.get("max_pages", DEFAULT_WEB_PAGES)
    if isinstance(raw_max_pages, bool):
        raise AuditRequestError("页面上限必须是 1 到 300 之间的整数。")
    try:
        max_pages = int(raw_max_pages)
    except (TypeError, ValueError) as exc:
        raise AuditRequestError("页面上限必须是 1 到 300 之间的整数。") from exc

    if not 1 <= max_pages <= MAX_WEB_PAGES:
        raise AuditRequestError("页面上限必须是 1 到 300 之间的整数。")
    return url, max_pages


class AuditAppHandler(SimpleHTTPRequestHandler):
    """Serve the single-page UI and its same-origin audit endpoint."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Avoid persisting visitor-provided target URLs in server logs."""

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if urlsplit(self.path).path == "/api/health":
            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "service": "searchscope",
                    "mode": "read_only",
                    "auditExecution": True,
                },
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/api/audit":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "接口不存在。"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "无效的 Content-Length。"})
            return
        if content_length <= 0 or content_length > MAX_BODY_BYTES:
            self.send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "请求内容过大或为空。"})
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            url, max_pages = parse_audit_request(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, AuditRequestError) as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        if not AUDIT_GATE.acquire(blocking=False):
            self.send_json(
                HTTPStatus.TOO_MANY_REQUESTS,
                {"error": "已有巡检正在执行，请在完成后再试。"},
            )
            return

        try:
            audit = audit_site(
                url,
                max_pages=max_pages,
                timeout=10,
                delay=0.1,
                max_bytes=5_000_000,
                max_sitemaps=10,
                allow_private=False,
            )
        except ValueError as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception:  # pragma: no cover - defensive boundary for the web process
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "巡检执行失败，请稍后重试。"})
            return
        finally:
            AUDIT_GATE.release()

        self.send_json(
            HTTPStatus.OK,
            {
                "audit": audit,
                "markdown": markdown_report(audit),
            },
        )


def main() -> int:
    raw_port = os.environ.get("PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError:
        port = 8000
    if not 1 <= port <= 65535:
        port = 8000

    server = ThreadingHTTPServer(("0.0.0.0", port), AuditAppHandler)
    print(f"SEO/GEO 巡检应用已启动：http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
