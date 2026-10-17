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
MAX_BODY_BYTES = 300_000
MAX_TARGET_URL_CHARS = 2_048
MAX_WEB_PAGES = 300
DEFAULT_WEB_PAGES = 25
WEB_TOTAL_TIMEOUT_SECONDS = 180
AUDIT_GATE = threading.BoundedSemaphore(value=1)
AUDIT_STATE_LOCK = threading.Lock()
CURRENT_AUDIT: "AuditRun | None" = None
LAST_AUDIT_STATUS: dict[str, Any] = {
    "running": False,
    "status": "idle",
    "phase": "idle",
    "pages_processed": 0,
    "max_pages": 0,
}

sys.path.insert(0, str(ENGINE_DIR))
from external_evidence import (  # noqa: E402
    ExternalEvidenceError,
    MAX_EXTERNAL_EVIDENCE_BYTES,
    summarize_external_evidence,
)
from site_audit import (  # noqa: E402
    AuditCancelledError,
    AuditTimeoutError,
    audit_site,
    markdown_report,
)


class AuditRequestError(ValueError):
    """Raised when a browser request cannot be safely audited."""


class AuditRun:
    """In-memory status and cancellation state for the single active audit."""

    def __init__(self, max_pages: int) -> None:
        self.cancel_event = threading.Event()
        self.running = True
        self.status = "running"
        self.phase = "preparing"
        self.pages_processed = 0
        self.max_pages = max_pages

    def snapshot(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "status": self.status,
            "phase": self.phase,
            "pages_processed": self.pages_processed,
            "max_pages": self.max_pages,
        }


def update_audit_progress(run: AuditRun, progress: dict[str, Any]) -> None:
    global LAST_AUDIT_STATUS
    with AUDIT_STATE_LOCK:
        run.phase = str(progress.get("phase") or "crawl")
        run.pages_processed = int(progress.get("pages_processed") or 0)
        run.max_pages = int(progress.get("max_pages") or run.max_pages)
        LAST_AUDIT_STATUS = run.snapshot()


def finish_audit(run: AuditRun, status: str) -> None:
    global CURRENT_AUDIT, LAST_AUDIT_STATUS
    with AUDIT_STATE_LOCK:
        run.running = False
        run.status = status
        run.phase = status
        LAST_AUDIT_STATUS = run.snapshot()
        if CURRENT_AUDIT is run:
            CURRENT_AUDIT = None


def current_audit_status() -> dict[str, Any]:
    with AUDIT_STATE_LOCK:
        if CURRENT_AUDIT is not None:
            return CURRENT_AUDIT.snapshot()
        return dict(LAST_AUDIT_STATUS)


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
    if len(url) > MAX_TARGET_URL_CHARS:
        raise AuditRequestError("网址过长，请检查后重试。")

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


def parse_browser_render_option(payload: dict[str, Any]) -> bool:
    """Accept only an explicit JSON boolean for optional browser rendering."""
    render_browser = payload.get("render_browser", False)
    if not isinstance(render_browser, bool):
        raise AuditRequestError("浏览器复核选项无效，请重新选择后重试。")
    return render_browser


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
        request_path = urlsplit(self.path).path
        if request_path == "/api/health":
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
        if request_path == "/api/audit/status":
            self.send_json(HTTPStatus.OK, current_audit_status())
            return
        if request_path == "/docs/external-evidence.md":
            content = (ROOT_DIR / "docs" / "external-evidence.md").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        request_path = urlsplit(self.path).path
        if request_path == "/api/audit/cancel":
            self.cancel_audit()
            return
        if request_path != "/api/audit":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "接口不存在。"})
            return

        if self.headers.get_content_type() != "application/json":
            self.send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "请求内容必须是 JSON。"})
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
            render_browser = parse_browser_render_option(payload)
            raw_external_evidence = payload.get("external_evidence")
            if raw_external_evidence is not None and len(
                json.dumps(raw_external_evidence, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ) > MAX_EXTERNAL_EVIDENCE_BYTES:
                raise ExternalEvidenceError("外部数据文件超过 256 KiB 限制。")
            external_evidence = summarize_external_evidence(
                raw_external_evidence,
                url,
            )
        except RecursionError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "请求 JSON 层级过深。"})
            return
        except (UnicodeDecodeError, ValueError) as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        if not AUDIT_GATE.acquire(blocking=False):
            self.send_json(
                HTTPStatus.TOO_MANY_REQUESTS,
                {"error": "已有巡检正在执行，请在完成后再试。"},
            )
            return

        global CURRENT_AUDIT
        run = AuditRun(max_pages)
        with AUDIT_STATE_LOCK:
            CURRENT_AUDIT = run
            LAST_AUDIT_STATUS.update(run.snapshot())

        final_status = "failed"
        try:
            audit = audit_site(
                url,
                max_pages=max_pages,
                timeout=10,
                delay=0.1,
                max_bytes=5_000_000,
                max_sitemaps=10,
                allow_private=False,
                render_browser=render_browser,
                total_timeout=WEB_TOTAL_TIMEOUT_SECONDS,
                should_cancel=run.cancel_event.is_set,
                on_progress=lambda progress: update_audit_progress(run, progress),
            )
            if external_evidence is not None:
                audit["external_evidence"] = external_evidence
            final_status = "completed"
        except AuditCancelledError:
            final_status = "cancelled"
            self.send_json(HTTPStatus.CONFLICT, {"error": "巡检已取消，没有生成部分成功报告。"})
            return
        except AuditTimeoutError:
            final_status = "timeout"
            self.send_json(
                HTTPStatus.GATEWAY_TIMEOUT,
                {"error": "巡检超过最长运行时限，已结束。请减少巡检页数后重试。"},
            )
            return
        except ValueError as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception:  # pragma: no cover - defensive boundary for the web process
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "巡检执行失败，请稍后重试。"})
            return
        finally:
            finish_audit(run, final_status)
            AUDIT_GATE.release()

        self.send_json(
            HTTPStatus.OK,
            {
                "audit": audit,
                "markdown": markdown_report(audit),
            },
        )

    def cancel_audit(self) -> None:
        if (
            self.headers.get_content_type() != "application/json"
            or self.headers.get("X-SearchScope-Request") != "same-origin"
        ):
            self.send_json(HTTPStatus.FORBIDDEN, {"error": "取消请求无效。"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "无效的 Content-Length。"})
            return
        if content_length <= 0 or content_length > 1024:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "取消请求内容无效。"})
            return
        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except RecursionError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "请求 JSON 层级过深。"})
            return
        except (UnicodeDecodeError, ValueError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "取消请求内容无效。"})
            return
        if not isinstance(payload, dict):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "取消请求内容无效。"})
            return

        with AUDIT_STATE_LOCK:
            run = CURRENT_AUDIT
            if run is not None:
                run.cancel_event.set()
        if run is None:
            self.send_json(
                HTTPStatus.CONFLICT,
                {"cancel_requested": False, "error": "当前没有正在执行的巡检。"},
            )
            return
        self.send_json(HTTPStatus.ACCEPTED, {"cancel_requested": True})


def main() -> int:
    raw_port = os.environ.get("PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError:
        port = 8000
    if not 1 <= port <= 65535:
        port = 8000

    server = ThreadingHTTPServer(("127.0.0.1", port), AuditAppHandler)
    print(f"SEO/GEO 巡检应用已启动：http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
