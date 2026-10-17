"""Optional, network-routed browser rendering for public site audits."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit


MAX_RENDER_PAGES = 10
MAX_BROWSER_REQUESTS_PER_PAGE = 40
MAX_BROWSER_RESOURCE_BYTES = 1_000_000
MAX_BROWSER_PAGE_BYTES = 5_000_000
MAX_RENDERED_DOM_CHARS = 5_000_000
RENDER_SETTLE_MILLISECONDS = 750
RENDER_NAVIGATION_TIMEOUT_MILLISECONDS = 15_000
RENDER_CONTENT_TIMEOUT_MILLISECONDS = 3_000
RENDER_FETCH_TIMEOUT_SECONDS = 3
ALLOWED_RESOURCE_TYPES = frozenset({"document", "script", "stylesheet", "xhr", "fetch"})
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
CONTENT_SECURITY_POLICY = (
    "sandbox allow-scripts allow-same-origin; "
    "default-src 'self' data: blob:; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "connect-src 'self'; img-src 'self' data:; font-src 'self' data:; "
    "media-src 'none'; object-src 'none'; frame-src 'none'; "
    "form-action 'none'; base-uri 'self'"
)
BLOCK_BROWSER_NETWORK_APIS = """
for (const name of ['RTCPeerConnection', 'webkitRTCPeerConnection']) {
  try {
    Object.defineProperty(window, name, {
      configurable: false,
      writable: false,
      value: undefined
    });
  } catch (_) {}
}
document.addEventListener('submit', event => event.preventDefault(), true);
"""


class BrowserRendererUnavailableError(ValueError):
    """Raised when the optional Playwright browser runtime is not installed."""


def _url_origin(url: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return ""
    try:
        parsed.port
        from site_audit import origin_for

        return origin_for(url)
    except (ImportError, ValueError):
        return ""


def _normalized_url(url: str) -> str:
    parsed = urlsplit(url)
    origin = urlsplit(_url_origin(url))
    if not origin.scheme or not origin.netloc:
        return ""
    return urlunsplit(
        (origin.scheme, origin.netloc, parsed.path or "/", parsed.query, "")
    )


def _load_playwright():  # noqa: ANN202
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BrowserRendererUnavailableError(
            "尚未安装可选浏览器组件。请按 docs/browser-rendering.md 安装 Playwright 和 Chromium。"
        ) from exc
    return sync_playwright, PlaywrightTimeoutError


def ensure_browser_runtime() -> None:
    """Fail before crawling if the optional package or its Chromium binary is absent."""
    sync_playwright, _ = _load_playwright()
    try:
        with sync_playwright() as playwright:
            executable = Path(playwright.chromium.executable_path)
    except Exception as exc:
        raise BrowserRendererUnavailableError(
            "无法检查 Chromium 浏览器。请按 docs/browser-rendering.md 重新安装可选浏览器组件。"
        ) from exc
    if not executable.is_file():
        raise BrowserRendererUnavailableError(
            "尚未安装 Chromium 浏览器。请执行 `python -m playwright install chromium` 后重试。"
        )


class BrowserPageRequestRouter:
    """Fulfill eligible browser requests only through the audit's safe fetcher."""

    def __init__(
        self,
        page_url: str,
        *,
        safe_fetcher: Callable[..., tuple[dict[str, Any], str | bytes]],
        user_agent: str,
        timeout: float = RENDER_FETCH_TIMEOUT_SECONDS,
        check_control: Callable[[], float | None] | None = None,
        max_requests: int = MAX_BROWSER_REQUESTS_PER_PAGE,
        max_resource_bytes: int = MAX_BROWSER_RESOURCE_BYTES,
        max_page_bytes: int = MAX_BROWSER_PAGE_BYTES,
    ) -> None:
        self.expected_url = _normalized_url(page_url)
        self.allowed_origin = _url_origin(page_url)
        if not self.allowed_origin:
            raise ValueError("Browser rendering requires an absolute public HTTP(S) URL")
        self.allowed_navigation_urls = {self.expected_url}
        self.safe_fetcher = safe_fetcher
        self.user_agent = user_agent
        self.timeout = timeout
        self.check_control = check_control
        self.max_requests = max_requests
        self.max_resource_bytes = max_resource_bytes
        self.max_page_bytes = max_page_bytes
        self.request_count = 0
        self.blocked_requests = 0
        self.bytes_loaded = 0

    def _abort(self, route: Any) -> None:
        self.blocked_requests += 1
        try:
            route.abort()
        except Exception:
            pass

    def handle(self, route: Any) -> None:
        self.request_count += 1
        if self.request_count > self.max_requests:
            self._abort(route)
            return

        request = route.request
        request_url = str(getattr(request, "url", ""))
        try:
            parsed = urlsplit(request_url)
            parsed.port
            normalized_request_url = _normalized_url(request_url)
        except (TypeError, ValueError):
            self._abort(route)
            return

        is_navigation = bool(request.is_navigation_request())
        if (
            str(getattr(request, "method", "")).upper() != "GET"
            or _url_origin(request_url) != self.allowed_origin
            or str(getattr(request, "resource_type", "")) not in ALLOWED_RESOURCE_TYPES
            or (is_navigation and normalized_request_url not in self.allowed_navigation_urls)
        ):
            self._abort(route)
            return
        if is_navigation:
            self.allowed_navigation_urls.discard(normalized_request_url)

        if self.check_control:
            try:
                self.check_control()
            except Exception:
                self._abort(route)
                raise

        remaining_bytes = self.max_page_bytes - self.bytes_loaded
        if remaining_bytes <= 0:
            self._abort(route)
            return
        max_bytes = min(self.max_resource_bytes, remaining_bytes)
        try:
            meta, body = self.safe_fetcher(
                request_url,
                timeout=self.timeout,
                max_bytes=max_bytes,
                user_agent=self.user_agent,
                allow_private=False,
                max_redirects=5,
                check_control=self.check_control,
                return_bytes=True,
                follow_redirects=False,
                allowed_origin=self.allowed_origin,
            )
        except Exception:
            if self.check_control:
                try:
                    self.check_control()
                except Exception:
                    self._abort(route)
                    raise
            self._abort(route)
            return

        if not isinstance(meta, dict) or meta.get("error"):
            self._abort(route)
            return
        status = meta.get("status")
        if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
            self._abort(route)
            return
        if meta.get("truncated") or not isinstance(body, bytes):
            self._abort(route)
            return
        if len(body) > max_bytes or self.bytes_loaded + len(body) > self.max_page_bytes:
            self._abort(route)
            return

        headers: dict[str, str] = {}
        content_type = str(meta.get("content_type") or "application/octet-stream")
        charset = meta.get("content_charset")
        if isinstance(charset, str) and re.fullmatch(r"[A-Za-z0-9._+-]{1,40}", charset):
            content_type = f"{content_type}; charset={charset}"
        headers["content-type"] = content_type

        if status in REDIRECT_STATUSES:
            redirect_url = meta.get("redirect_url")
            if not isinstance(redirect_url, str) or _url_origin(redirect_url) != self.allowed_origin:
                self._abort(route)
                return
            headers["location"] = redirect_url
            if is_navigation:
                self.allowed_navigation_urls.add(_normalized_url(redirect_url))
        elif is_navigation:
            headers["content-security-policy"] = CONTENT_SECURITY_POLICY

        self.bytes_loaded += len(body)
        try:
            route.fulfill(status=status, headers=headers, body=body)
        except Exception:
            self._abort(route)


def _rendered_fields(static_page: dict[str, Any], rendered_page: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "title",
        "title_length",
        "meta_description",
        "meta_description_length",
        "canonical",
        "html_lang",
        "robots_directive",
        "noindex",
        "h1_count",
        "h1",
        "json_ld_static_count",
        "json_ld_static_valid_count",
    )
    differences = [
        field
        for field in (
            "title",
            "meta_description",
            "canonical",
            "html_lang",
            "robots_directive",
            "h1",
            "json_ld_static_count",
        )
        if static_page.get(field) != rendered_page.get(field)
    ]
    return {
        **{field: rendered_page.get(field) for field in fields},
        "differences": differences,
    }


def render_browser_pages(
    pages: list[dict[str, Any]],
    *,
    site_origin: str,
    user_agent: str,
    timeout: float,
    check_control: Callable[[], float | None],
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    safe_fetcher: Callable[..., tuple[dict[str, Any], str | bytes]] | None = None,
) -> dict[str, Any]:
    """Render a capped same-origin page sample and return aggregate observations."""
    from site_audit import (
        AuditCancelledError,
        AuditTimeoutError,
        fetch_url,
        normalized_url,
        parse_html,
        same_origin,
    )

    sync_playwright, playwright_timeout_error = _load_playwright()
    safe_fetcher = safe_fetcher or fetch_url
    eligible = [
        page
        for page in pages
        if page.get("is_html")
        and not page.get("error")
        and not page.get("blocked_by_robots")
        and page.get("final_url")
        and same_origin(site_origin, str(page["final_url"]))
    ]
    selected = eligible[:MAX_RENDER_PAGES]
    progress_max = len(selected)
    if on_progress:
        on_progress({"phase": "browser_render", "pages_processed": 0, "max_pages": progress_max})

    result = {
        "enabled": True,
        "eligible_pages": len(eligible),
        "sampled_pages": len(selected),
        "rendered_pages": 0,
        "failed_pages": 0,
        "pages_not_sampled": max(0, len(eligible) - len(selected)),
        "blocked_requests": 0,
        "affects_score": False,
        "rendered_html_retained": False,
    }
    if not selected:
        return result

    browser = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    "--host-resolver-rules=MAP * ~NOTFOUND",
                    "--disable-background-networking",
                ],
            )
            for index, audit_page in enumerate(selected, start=1):
                check_control()
                requested_url = normalized_url(str(audit_page["final_url"]))
                router = BrowserPageRequestRouter(
                    requested_url,
                    safe_fetcher=safe_fetcher,
                    user_agent=user_agent,
                    timeout=min(RENDER_FETCH_TIMEOUT_SECONDS, timeout),
                    check_control=check_control,
                )
                context = browser.new_context(
                    user_agent=user_agent,
                    service_workers="block",
                    accept_downloads=False,
                )
                context.route_web_socket(
                    "**/*",
                    lambda websocket: websocket.close(
                        code=1000,
                        reason="SearchScope blocks WebSocket traffic",
                    ),
                )
                context.route("**/*", router.handle)
                page = context.new_page()
                context.on("page", lambda popup: popup.close())
                page.on("dialog", lambda dialog: dialog.dismiss())
                page.add_init_script(BLOCK_BROWSER_NETWORK_APIS)
                page.set_default_timeout(RENDER_CONTENT_TIMEOUT_MILLISECONDS)
                page_result: dict[str, Any] = {
                    "status": "failed",
                    "error": "浏览器渲染未能完成。",
                    "blocked_requests": 0,
                    "bytes_loaded": 0,
                }
                try:
                    remaining = check_control()
                    navigation_timeout = RENDER_NAVIGATION_TIMEOUT_MILLISECONDS
                    if remaining is not None:
                        navigation_timeout = max(1, min(navigation_timeout, int(remaining * 1000)))
                    response = page.goto(
                        requested_url,
                        wait_until="domcontentloaded",
                        timeout=navigation_timeout,
                    )
                    if response is None:
                        raise RuntimeError("No document response")
                    page.wait_for_timeout(RENDER_SETTLE_MILLISECONDS)
                    check_control()
                    rendered_html = page.locator("html").inner_html(
                        timeout=RENDER_CONTENT_TIMEOUT_MILLISECONDS
                    )
                    if len(rendered_html) > MAX_RENDERED_DOM_CHARS:
                        raise RuntimeError("Rendered DOM exceeded the size limit")
                    rendered_fields, _ = parse_html(page.url or requested_url, rendered_html)
                    rendered_fields["html_lang"] = (
                        page.locator("html").get_attribute(
                            "lang",
                            timeout=RENDER_CONTENT_TIMEOUT_MILLISECONDS,
                        )
                        or ""
                    )
                    page_result = {
                        "status": "completed",
                        "http_status": response.status,
                        "error": None,
                        "blocked_requests": router.blocked_requests,
                        "bytes_loaded": router.bytes_loaded,
                        **_rendered_fields(audit_page, rendered_fields),
                    }
                    result["rendered_pages"] += 1
                except playwright_timeout_error:
                    check_control()
                    page_result["error"] = "页面渲染超过限定时间。"
                    result["failed_pages"] += 1
                except Exception:
                    check_control()
                    page_result["error"] = "页面渲染未能完成。"
                    result["failed_pages"] += 1
                finally:
                    page_result["blocked_requests"] = router.blocked_requests
                    page_result["bytes_loaded"] = router.bytes_loaded
                    audit_page["browser_render"] = page_result
                    result["blocked_requests"] += router.blocked_requests
                    if on_progress:
                        on_progress(
                            {
                                "phase": "browser_render",
                                "pages_processed": index,
                                "max_pages": progress_max,
                            }
                        )
                    try:
                        context.close()
                    except Exception:
                        pass
                check_control()
    except (BrowserRendererUnavailableError, AuditCancelledError, AuditTimeoutError):
        raise
    except Exception as exc:
        raise BrowserRendererUnavailableError(
            "无法启动或控制 Chromium 浏览器。请按 docs/browser-rendering.md 检查可选浏览器安装。"
        ) from exc
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass

    return result
