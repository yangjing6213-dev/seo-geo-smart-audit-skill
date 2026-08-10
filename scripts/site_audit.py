#!/usr/bin/env python3
"""Bounded, read-only SEO/GEO crawler using only the Python standard library."""

from __future__ import annotations

import argparse
from collections import Counter, deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.client import HTTPConnection, HTTPSConnection
import ipaddress
import json
import math
from pathlib import Path
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import (
    HTTPHandler,
    HTTPRedirectHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
)
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

from html_report import html_report


DEFAULT_USER_AGENT = "IndependentSiteSeoGeoAudit/1.0 (+read-only)"
ENGINE_VERSION = "1.4.9"
MAX_REQUEST_TIMEOUT = 604800
WATCHDOG_JOIN_TIMEOUT = 0.2
REQUEST_TIMEOUT_ERROR = (
    "Per-request timeout must be finite, greater than 0, and no more than 604800 seconds"
)
MAX_REDIRECTS_ERROR = "max_redirects must be a non-negative integer"
AI_BOTS = {
    "search": ("OAI-SearchBot", "PerplexityBot"),
    "training": ("GPTBot", "Google-Extended", "ClaudeBot"),
    "user_fetch": ("ChatGPT-User", "Claude-User"),
}
MACHINE_ASSETS = ("/llms.txt", "/pricing.md", "/okf/index.md")
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
KNOWN_METADATA_ADDRESSES = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("100.100.100.200"),
}
DNS_RESOLVER_SCRIPT = """\
import json
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
print(json.dumps([
    [family, socktype, proto, canonname, list(sockaddr)]
    for family, socktype, proto, canonname, sockaddr in addresses
]))
"""


class AuditCancelledError(RuntimeError):
    """Raised when a managed audit receives a cooperative cancellation."""


class AuditTimeoutError(RuntimeError):
    """Raised when a managed audit exceeds its total execution time."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


class AuditHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.h1_parts: list[list[str]] = []
        self.h2_count = 0
        self.meta: dict[str, str] = {}
        self.links: list[dict[str, str]] = []
        self.anchors: list[str] = []
        self.images_missing_alt = 0
        self.html_lang = ""
        self.json_ld_blocks: list[str] = []
        self.visible_text: list[str] = []
        self._capture_title = False
        self._capture_h1: list[str] | None = None
        self._capture_json: list[str] | None = None
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "html":
            self.html_lang = values.get("lang", "").strip()
        elif tag == "title":
            self._capture_title = True
        elif tag == "h1":
            self._capture_h1 = []
            self.h1_parts.append(self._capture_h1)
        elif tag == "h2":
            self.h2_count += 1
        elif tag == "meta":
            key = (values.get("name") or values.get("property") or "").strip().lower()
            if key:
                self.meta[key] = values.get("content", "").strip()
        elif tag == "link":
            self.links.append(
                {
                    "rel": values.get("rel", "").strip().lower(),
                    "href": values.get("href", "").strip(),
                    "hreflang": values.get("hreflang", "").strip(),
                }
            )
        elif tag == "a" and values.get("href"):
            self.anchors.append(values["href"].strip())
        elif tag == "img" and "alt" not in values:
            self.images_missing_alt += 1
        if tag == "script":
            self._ignored_depth += 1
            if values.get("type", "").lower() == "application/ld+json":
                self._capture_json = []
        elif tag in {"style", "noscript"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._capture_title = False
        elif tag == "h1":
            self._capture_h1 = None
        if tag == "script":
            if self._capture_json is not None:
                self.json_ld_blocks.append("".join(self._capture_json).strip())
                self._capture_json = None
            self._ignored_depth = max(0, self._ignored_depth - 1)
        elif tag in {"style", "noscript"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self.title_parts.append(data)
        if self._capture_h1 is not None:
            self._capture_h1.append(data)
        if self._capture_json is not None:
            self._capture_json.append(data)
        if not self._ignored_depth:
            text = " ".join(data.split())
            if text:
                self.visible_text.append(text)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalized_url(url: str) -> str:
    parsed = urlsplit(url)
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def origin_for(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), "", "", ""))


def same_origin(left: str, right: str) -> bool:
    return origin_for(left) == origin_for(right)


def validate_url_structure(url: str):
    try:
        parsed = urlsplit(url)
        has_credentials = parsed.username is not None or parsed.password is not None
    except ValueError:
        raise ValueError("Only absolute http/https URLs are allowed") from None
    if has_credentials:
        raise ValueError("URLs containing credentials are not allowed")
    try:
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        raise ValueError("Only absolute http/https URLs are allowed") from None
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ValueError("Only absolute http/https URLs are allowed")
    return parsed


def terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.kill()
    process.communicate()


def validate_request_timeout(timeout: Any) -> float:
    try:
        value = float(timeout)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(REQUEST_TIMEOUT_ERROR) from None
    if not math.isfinite(value) or value <= 0 or value > MAX_REQUEST_TIMEOUT:
        raise ValueError(REQUEST_TIMEOUT_ERROR)
    return value


def validate_max_redirects(max_redirects: Any) -> int:
    if isinstance(max_redirects, bool) or not isinstance(max_redirects, int):
        raise ValueError(MAX_REDIRECTS_ERROR)
    if max_redirects < 0:
        raise ValueError(MAX_REDIRECTS_ERROR)
    return max_redirects


def parse_max_redirects(value: str) -> int:
    try:
        parsed = int(value)
        return validate_max_redirects(parsed)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(MAX_REDIRECTS_ERROR) from None


def resolve_hostname(
    hostname: str,
    port: int,
    check_control: Callable[[], float | None] | None,
    timeout: float,
) -> tuple[tuple[Any, ...], ...]:
    timeout = validate_request_timeout(timeout)
    try:
        ipaddress.ip_address(hostname.split("%", 1)[0])
    except ValueError:
        is_numeric = False
    else:
        is_numeric = True

    if is_numeric:
        addresses = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
            flags=socket.AI_NUMERICHOST,
        )
    else:
        if check_control:
            check_control()
        resolver_deadline = time.monotonic() + max(0, timeout)
        creation_flags = (
            subprocess.CREATE_NO_WINDOW
            if sys.platform == "win32"
            else 0
        )
        process = subprocess.Popen(
            [sys.executable, "-I", "-c", DNS_RESOLVER_SCRIPT, hostname, str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creation_flags,
        )
        try:
            while True:
                remaining_total = check_control() if check_control else None
                remaining_request = resolver_deadline - time.monotonic()
                if remaining_request <= 0:
                    raise TimeoutError("DNS resolution timed out")
                wait_timeout = min(0.05, remaining_request)
                if remaining_total is not None:
                    wait_timeout = min(wait_timeout, max(0.001, remaining_total))
                try:
                    stdout, stderr = process.communicate(timeout=wait_timeout)
                    break
                except subprocess.TimeoutExpired:
                    continue
            if check_control:
                check_control()
        except BaseException:
            terminate_process(process)
            raise
        if process.returncode:
            raise ValueError("DNS resolution failed")
        try:
            records = json.loads(stdout)
            addresses = [
                (
                    int(family),
                    int(socktype),
                    int(proto),
                    str(canonname),
                    tuple(sockaddr),
                )
                for family, socktype, proto, canonname, sockaddr in records
            ]
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("DNS resolution returned invalid data") from exc
    return tuple(addresses)


def resolve_url(
    url: str,
    allow_private: bool,
    check_control: Callable[[], float | None] | None = None,
    timeout: float = 10.0,
) -> tuple[tuple[Any, ...], ...]:
    timeout = validate_request_timeout(timeout)
    parsed = validate_url_structure(url)
    try:
        addresses = resolve_hostname(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            check_control,
            timeout,
        )
    except socket.gaierror as exc:
        raise ValueError("DNS resolution failed") from exc
    usable_addresses = tuple(
        item
        for item in addresses
        if item[0] in {socket.AF_INET, socket.AF_INET6}
        and item[1] == socket.SOCK_STREAM
    )
    if not usable_addresses:
        raise ValueError("DNS resolution returned no usable address")
    if allow_private:
        return usable_addresses
    for item in usable_addresses:
        address = ipaddress.ip_address(str(item[4][0]).split("%", 1)[0])
        if not address.is_global or address in KNOWN_METADATA_ADDRESSES:
            raise ValueError("Private or non-public address blocked")
    return usable_addresses


def validate_url(url: str, allow_private: bool) -> None:
    resolve_url(url, allow_private)


def controlled_sleep(
    duration: float,
    check_control: Callable[[], float | None],
) -> None:
    wake_at = time.monotonic() + duration
    while True:
        remaining_total = check_control()
        remaining_delay = wake_at - time.monotonic()
        if remaining_delay <= 0:
            break
        sleep_for = min(0.05, remaining_delay)
        if remaining_total is not None:
            sleep_for = min(sleep_for, max(0.001, remaining_total))
        time.sleep(sleep_for)
    check_control()


def connect_resolved(
    addresses: tuple[tuple[Any, ...], ...],
    timeout: float | None | object,
    source_address: tuple[str, int] | None,
) -> socket.socket:
    validated_timeout = (
        validate_request_timeout(timeout)
        if timeout is not None and timeout is not socket._GLOBAL_DEFAULT_TIMEOUT
        else None
    )
    deadline = (
        time.monotonic() + validated_timeout
        if validated_timeout is not None
        else None
    )
    last_error: OSError | None = None
    for family, socktype, proto, _, sockaddr in addresses:
        sock = socket.socket(family, socktype, proto)
        try:
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("timed out")
                sock.settimeout(max(0.001, remaining))
            elif timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last_error = exc
            sock.close()
        except BaseException:
            sock.close()
            raise
    if last_error:
        raise last_error
    raise OSError("No validated address available")


class PinnedHTTPConnection(HTTPConnection):
    def __init__(
        self,
        host: str,
        port: int | None = None,
        *,
        resolved_addresses: tuple[tuple[Any, ...], ...],
        **kwargs: Any,
    ) -> None:
        super().__init__(host, port, **kwargs)
        self._create_connection = lambda _address, timeout, source_address: connect_resolved(
            resolved_addresses,
            timeout,
            source_address,
        )


class PinnedHTTPSConnection(HTTPSConnection):
    def __init__(
        self,
        host: str,
        port: int | None = None,
        *,
        resolved_addresses: tuple[tuple[Any, ...], ...],
        **kwargs: Any,
    ) -> None:
        super().__init__(host, port, **kwargs)
        self._create_connection = lambda _address, timeout, source_address: connect_resolved(
            resolved_addresses,
            timeout,
            source_address,
        )

    def connect(self) -> None:
        try:
            super().connect()
        except BaseException:
            if self.sock is not None:
                self.sock.close()
                self.sock = None
            raise


class PinnedHTTPHandler(HTTPHandler):
    def __init__(self, resolved_addresses: tuple[tuple[Any, ...], ...]) -> None:
        super().__init__()
        self.resolved_addresses = resolved_addresses

    def http_open(self, request):  # noqa: ANN001
        return self.do_open(
            lambda host, **kwargs: PinnedHTTPConnection(
                host,
                resolved_addresses=self.resolved_addresses,
                **kwargs,
            ),
            request,
        )


class PinnedHTTPSHandler(HTTPSHandler):
    def __init__(
        self,
        resolved_addresses: tuple[tuple[Any, ...], ...],
        context: ssl.SSLContext,
    ) -> None:
        super().__init__(context=context)
        self.resolved_addresses = resolved_addresses

    def https_open(self, request):  # noqa: ANN001
        return self.do_open(
            lambda host, **kwargs: PinnedHTTPSConnection(
                host,
                resolved_addresses=self.resolved_addresses,
                **kwargs,
            ),
            request,
            context=self._context,
        )


def response_socket(response: Any) -> socket.socket | None:
    pending = [response]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, socket.socket):
            return current
        for attribute in ("fp", "raw", "_sock", "file"):
            child = getattr(current, attribute, None)
            if child is not None:
                pending.append(child)
    return None


class ResponseBodyWatchdog:
    def __init__(
        self,
        sock: socket.socket,
        check_control: Callable[[], float | None],
    ) -> None:
        self.sock = sock
        self.check_control = check_control
        self.stop_event = threading.Event()
        self.error: AuditCancelledError | AuditTimeoutError | None = None
        self.thread = threading.Thread(
            target=self._run,
            name="seo-audit-body-watchdog",
            daemon=True,
        )

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                remaining = self.check_control()
            except (AuditCancelledError, AuditTimeoutError) as exc:
                self.error = exc
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    descriptor = self.sock.detach()
                    socket.close(descriptor)
                except (OSError, ValueError):
                    try:
                        self.sock.close()
                    except OSError:
                        pass
                return
            wait_for = 0.05 if remaining is None else min(0.05, max(0.001, remaining))
            if self.stop_event.wait(wait_for):
                return

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=WATCHDOG_JOIN_TIMEOUT)


def read_response_body(
    response: Any,
    *,
    timeout: float,
    max_bytes: int,
    check_control: Callable[[], float | None] | None,
) -> bytes:
    chunks: list[bytes] = []
    bytes_remaining = max_bytes + 1
    reader = getattr(response, "read1", None)
    if not callable(reader):
        reader = response.read
    sock = response_socket(response)
    if sock:
        sock.settimeout(timeout)
    watchdog = (
        ResponseBodyWatchdog(sock, check_control)
        if sock is not None and check_control is not None
        else None
    )
    if watchdog:
        watchdog.start()
    try:
        while bytes_remaining > 0:
            if check_control:
                check_control()
            chunk = reader(min(64 * 1024, bytes_remaining))
            if check_control:
                check_control()
            if not chunk:
                break
            chunks.append(chunk)
            bytes_remaining -= len(chunk)
    except Exception:
        if watchdog and watchdog.error:
            raise watchdog.error
        raise
    finally:
        if watchdog:
            watchdog.stop()
    if watchdog and watchdog.error:
        raise watchdog.error
    return b"".join(chunks)


def fetch_url(
    url: str,
    *,
    timeout: float,
    max_bytes: int,
    user_agent: str,
    allow_private: bool,
    max_redirects: int = 5,
    check_control: Callable[[], float | None] | None = None,
) -> tuple[dict[str, Any], str]:
    timeout = validate_request_timeout(timeout)
    candidate = url
    validate_url_structure(candidate)
    candidate = normalized_url(candidate)
    max_redirects = validate_max_redirects(max_redirects)
    history: list[dict[str, Any]] = []
    context = ssl.create_default_context()
    started = time.perf_counter()
    try:
        remaining = check_control() if check_control else None
        resolved_addresses = resolve_url(
            candidate,
            allow_private,
            check_control,
            timeout,
        )
        current = candidate
    except (URLError, TimeoutError, OSError) as exc:
        if check_control:
            check_control()
        return (
            {
                "requested_url": None,
                "final_url": None,
                "status": None,
                "error": (
                    "Target resolution timed out"
                    if isinstance(exc, TimeoutError)
                    else "Target resolution failed"
                ),
                "redirects": history,
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
            },
            "",
        )

    while True:
        started = time.perf_counter()
        response = None
        try:
            remaining = check_control() if check_control else None
            opener = build_opener(
                ProxyHandler({}),
                NoRedirect(),
                PinnedHTTPHandler(resolved_addresses),
                PinnedHTTPSHandler(resolved_addresses, context),
            )
            request = Request(
                current,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.1",
                    "Accept-Encoding": "identity",
                },
            )
            request_timeout = timeout if remaining is None else min(timeout, max(0.001, remaining))
            try:
                response = opener.open(request, timeout=request_timeout)
            except HTTPError as exc:
                response = exc
            status = int(response.status)
            headers = response.headers
            body = (
                b""
                if status in REDIRECT_STATUSES
                else read_response_body(
                    response,
                    timeout=request_timeout,
                    max_bytes=max_bytes,
                    check_control=check_control,
                )
            )
        except (URLError, TimeoutError, OSError) as exc:
            if check_control:
                check_control()
            return (
                {
                    "requested_url": url,
                    "final_url": current,
                    "status": None,
                    "error": str(exc),
                    "redirects": history,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000),
                },
                "",
            )
        finally:
            if response is not None:
                response.close()

        elapsed_ms = round((time.perf_counter() - started) * 1000)
        if status in REDIRECT_STATUSES and headers.get("Location"):
            try:
                next_url = normalized_url(urljoin(current, headers["Location"]))
                next_resolved_addresses = resolve_url(
                    next_url,
                    allow_private,
                    check_control,
                    timeout,
                )
            except (ValueError, URLError, TimeoutError, OSError) as exc:
                if check_control:
                    check_control()
                return (
                    {
                        "requested_url": url,
                        "final_url": current,
                        "status": None,
                        "error": (
                            "Redirect target resolution timed out"
                            if isinstance(exc, TimeoutError)
                            else "Redirect target validation failed"
                        ),
                        "redirects": history,
                        "elapsed_ms": elapsed_ms,
                    },
                    "",
                )
            if len(history) >= max_redirects:
                return (
                    {
                        "requested_url": url,
                        "final_url": current,
                        "status": None,
                        "error": f"Too many redirects (limit: {max_redirects})",
                        "redirects": history,
                        "elapsed_ms": elapsed_ms,
                    },
                    "",
                )
            history.append({"status": status, "from": current, "to": next_url})
            current = next_url
            resolved_addresses = next_resolved_addresses
            continue

        truncated = len(body) > max_bytes
        body = body[:max_bytes]
        content_type = headers.get_content_type() if hasattr(headers, "get_content_type") else ""
        charset = headers.get_content_charset() if hasattr(headers, "get_content_charset") else None
        try:
            text = body.decode(charset or "utf-8", errors="replace")
        except LookupError:
            text = body.decode("utf-8", errors="replace")
        return (
            {
                "requested_url": url,
                "final_url": current,
                "status": status,
                "content_type": content_type,
                "bytes_read": len(body),
                "truncated": truncated,
                "redirects": history,
                "elapsed_ms": elapsed_ms,
                "error": None,
            },
            text,
        )


def parse_html(url: str, text: str) -> tuple[dict[str, Any], list[str]]:
    parser = AuditHTMLParser()
    try:
        parser.feed(text)
    except Exception as exc:  # HTMLParser should be tolerant; retain partial evidence.
        parse_error = str(exc)
    else:
        parse_error = None

    canonical_links = [link for link in parser.links if "canonical" in link["rel"].split()]
    canonical = urljoin(url, canonical_links[0]["href"]) if canonical_links and canonical_links[0]["href"] else ""
    hreflang = [
        {"lang": link["hreflang"], "url": normalized_url(urljoin(url, link["href"]))}
        for link in parser.links
        if "alternate" in link["rel"].split() and link["hreflang"] and link["href"]
    ]
    json_ld_valid = 0
    json_ld_errors: list[str] = []
    for block in parser.json_ld_blocks:
        try:
            json.loads(block)
            json_ld_valid += 1
        except (json.JSONDecodeError, TypeError) as exc:
            json_ld_errors.append(str(exc))

    internal_links: list[str] = []
    external_links = 0
    for href in parser.anchors:
        absolute = normalized_url(urljoin(url, href))
        parsed = urlsplit(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        if same_origin(url, absolute):
            internal_links.append(absolute)
        else:
            external_links += 1

    title = " ".join(" ".join(parser.title_parts).split())
    h1_values = [" ".join(" ".join(parts).split()) for parts in parser.h1_parts]
    description = parser.meta.get("description", "")
    robots_directive = ",".join(
        value for key, value in parser.meta.items() if key in {"robots", "googlebot", "bingbot"} and value
    ).lower()
    visible_text = " ".join(parser.visible_text)
    word_count = len(re.findall(r"[\w\u3400-\u9fff]+", visible_text, flags=re.UNICODE))
    has_author_signal = bool(
        parser.meta.get("author")
        or parser.meta.get("article:author")
        or re.search(r"\b(author|byline)\b|作者|撰稿", text, flags=re.IGNORECASE)
    )

    return (
        {
            "title": title,
            "title_length": len(title),
            "meta_description": description,
            "meta_description_length": len(description),
            "canonical": normalized_url(canonical) if canonical else "",
            "html_lang": parser.html_lang,
            "robots_directive": robots_directive,
            "noindex": "noindex" in robots_directive,
            "h1_count": len(h1_values),
            "h1": h1_values,
            "h2_count": parser.h2_count,
            "images_missing_alt_attribute": parser.images_missing_alt,
            "internal_link_count": len(set(internal_links)),
            "external_link_count": external_links,
            "hreflang": hreflang,
            "json_ld_static_count": len(parser.json_ld_blocks),
            "json_ld_static_valid_count": json_ld_valid,
            "json_ld_static_errors": json_ld_errors,
            "word_count": word_count,
            "author_signal": has_author_signal,
            "parse_error": parse_error,
        },
        list(dict.fromkeys(internal_links)),
    )


def parse_sitemap(text: str) -> tuple[str, list[str]]:
    root = ET.fromstring(text)
    kind = root.tag.split("}")[-1].lower()
    locations = [
        (element.text or "").strip()
        for element in root.iter()
        if element.tag.split("}")[-1].lower() == "loc" and (element.text or "").strip()
    ]
    return kind, locations


def build_page_scope(audit: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical, indexable page set used by page-level rules."""
    all_html_pages = [
        page
        for page in audit["pages"]
        if page.get("is_html") and page.get("status") == 200
    ]
    noindex_pages: list[dict[str, Any]] = []
    canonical_away_pages: list[dict[str, Any]] = []
    external_canonical_pages: list[dict[str, Any]] = []
    redirected_pages: list[dict[str, Any]] = []
    candidates: dict[str, list[dict[str, Any]]] = {}

    for page in all_html_pages:
        requested_url = normalized_url(page["url"])
        final_url = normalized_url(page.get("final_url") or requested_url)
        canonical = normalized_url(page.get("canonical") or final_url)
        if page.get("redirects") or requested_url != final_url:
            redirected_pages.append(page)
        if page.get("noindex"):
            noindex_pages.append(page)
            continue
        if not same_origin(final_url, canonical):
            external_canonical_pages.append(page)
            continue
        if canonical != final_url:
            canonical_away_pages.append(page)
            continue
        candidates.setdefault(canonical, []).append(page)

    def representative_rank(page: dict[str, Any]) -> tuple[int, int, str]:
        requested_url = normalized_url(page["url"])
        final_url = normalized_url(page.get("final_url") or requested_url)
        redirects = page.get("redirects") or []
        return (
            0 if requested_url == final_url and not redirects else 1,
            len(redirects),
            requested_url,
        )

    representatives = {
        identity: sorted(group, key=representative_rank)[0]
        for identity, group in candidates.items()
    }
    analysis_pages = list(representatives.values())
    identity_by_page_id = {id(page): identity for identity, page in representatives.items()}
    indexable_page_ids = set(identity_by_page_id)

    lookup: dict[str, dict[str, Any]] = {}
    for page in sorted(all_html_pages, key=representative_rank):
        requested_url = normalized_url(page["url"])
        final_url = normalized_url(page.get("final_url") or requested_url)
        lookup.setdefault(requested_url, page)
        lookup.setdefault(final_url, page)

    sitemap_urls = {normalized_url(url) for url in audit["discovery"]["sitemap_urls"]}
    return {
        "all_html_pages": all_html_pages,
        "analysis_pages": analysis_pages,
        "identity_by_page_id": identity_by_page_id,
        "indexable_page_ids": indexable_page_ids,
        "lookup": lookup,
        "noindex_pages": noindex_pages,
        "canonical_away_pages": canonical_away_pages,
        "external_canonical_pages": external_canonical_pages,
        "redirected_pages": redirected_pages,
        "sitemap_urls": sitemap_urls,
        "summary": {
            "html_pages": len(all_html_pages),
            "canonical_indexable_pages": len(analysis_pages),
            "redirect_aliases_excluded": len(redirected_pages),
            "noindex_excluded": len(noindex_pages),
            "canonical_away_excluded": len(canonical_away_pages),
            "external_canonical_excluded": len(external_canonical_pages),
        },
    }


def add_finding(
    findings: list[dict[str, Any]],
    *,
    code: str,
    category: str,
    severity: str,
    status: str,
    issue: str,
    evidence: Any,
    action: str,
    verification: str,
) -> None:
    findings.append(
        {
            "id": f"F{len(findings) + 1:03d}",
            "code": code,
            "category": category,
            "severity": severity,
            "status": status,
            "issue": issue,
            "evidence": evidence,
            "action": action,
            "verification": verification,
        }
    )


def add_strength(
    strengths: list[dict[str, Any]],
    *,
    code: str,
    category: str,
    title: str,
    evidence: Any,
    value: str,
) -> None:
    strengths.append(
        {
            "id": f"S{len(strengths) + 1:03d}",
            "code": code,
            "category": category,
            "status": "verified",
            "title": title,
            "evidence": evidence,
            "value": value,
        }
    )


def build_findings(audit: dict[str, Any], scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    pages = audit["pages"]
    scope = scope or build_page_scope(audit)
    html_pages = scope["analysis_pages"]
    all_html_pages = scope["all_html_pages"]
    sitemap_urls = scope["sitemap_urls"]

    robots = audit["discovery"]["robots"]
    if robots.get("status") != 200:
        robots_missing = robots.get("status") == 404
        add_finding(
            findings,
            code="robots_unavailable",
            category="crawlability",
            severity="info" if robots_missing else "medium",
            status="verified",
            issue="未提供 robots.txt，当前没有显式抓取策略" if robots_missing else "robots.txt 不可正常读取",
            evidence={"url": robots.get("final_url") or robots.get("requested_url"), "status": robots.get("status"), "error": robots.get("error")},
            action=(
                "如果需要声明抓取边界或 sitemap 地址，则在站点根目录提供 robots.txt；否则记录 404 为有意配置。"
                if robots_missing
                else "恢复站点根目录 robots.txt 的稳定访问，并确认策略及 sitemap 地址。"
            ),
            verification=(
                "确认 404 符合业务意图，或请求 /robots.txt 并验证状态为 200、语法可解析。"
                if robots_missing
                else "请求 /robots.txt，确认状态为 200、语法可解析且策略符合业务意图。"
            ),
        )

    valid_sitemaps = [
        item
        for item in audit["discovery"]["sitemaps"]
        if item.get("status") == 200 and item.get("kind") in {"urlset", "sitemapindex"}
    ]
    if not valid_sitemaps:
        add_finding(
            findings,
            code="sitemap_unavailable",
            category="crawlability",
            severity="medium",
            status="verified",
            issue="未发现可解析的 XML Sitemap",
            evidence=audit["discovery"]["sitemaps"],
            action="生成仅包含规范、可索引、返回 200 URL 的 XML Sitemap，并在 robots.txt 中声明。",
            verification="重新请求 sitemap，确认 XML 可解析、URL 属于本域且与索引策略一致。",
        )

    if audit["discovery"]["sitemap_duplicate_url_count"]:
        add_finding(
            findings,
            code="sitemap_duplicate_urls",
            category="technical_seo",
            severity="medium",
            status="verified",
            issue="Sitemap 含重复 URL",
            evidence=audit["discovery"]["sitemap_duplicate_urls"],
            action="去重 sitemap 的 loc，并保留唯一规范 URL。",
            verification="重新解析 sitemap，确认总 loc 数与唯一 loc 数相同。",
        )

    failed = [page for page in pages if page.get("status") is None or int(page["status"]) >= 400]
    if failed:
        add_finding(
            findings,
            code="failed_pages",
            category="crawlability",
            severity="high",
            status="verified",
            issue="已发现失败或错误响应页面",
            evidence=[{"url": p["url"], "status": p.get("status"), "error": p.get("error")} for p in failed[:20]],
            action="优先修复 sitemap 和核心导航中的失败 URL；有替代页时设置单跳 301。",
            verification="逐个请求受影响 URL，并确认最终状态、跳转链与 canonical。",
        )

    sitemap_noindex = [
        page["url"]
        for page in all_html_pages
        if page.get("noindex") and normalized_url(page["url"]) in sitemap_urls
    ]
    if sitemap_noindex:
        add_finding(
            findings,
            code="sitemap_noindex_conflict",
            category="indexation",
            severity="high",
            status="verified",
            issue="Sitemap URL 同时声明 noindex",
            evidence=sitemap_noindex[:20],
            action="根据页面意图移除 noindex 或从 sitemap 删除该 URL。",
            verification="确认页面索引指令与 sitemap 收录策略一致。",
        )

    missing_title = [page["url"] for page in html_pages if not page.get("title")]
    if missing_title:
        add_finding(
            findings,
            code="missing_title",
            category="on_page",
            severity="high",
            status="verified",
            issue="HTML 页面缺少 title",
            evidence=missing_title[:20],
            action="为每个可索引页面生成唯一且符合页面意图的 title。",
            verification="抓取页面并确认渲染前后 title 存在且唯一。",
        )

    missing_description = [page["url"] for page in html_pages if not page.get("meta_description")]
    if missing_description:
        add_finding(
            findings,
            code="missing_meta_description",
            category="on_page",
            severity="medium",
            status="verified",
            issue="部分 HTML 页面缺少 meta description",
            evidence=missing_description[:20],
            action="为重要可索引页面编写唯一、准确且与搜索意图一致的摘要，避免模板化堆词。",
            verification="重新抓取并确认重要页面 description 存在、唯一且与可见内容一致。",
        )

    missing_canonical = [page["url"] for page in html_pages if not page.get("canonical")]
    if missing_canonical:
        add_finding(
            findings,
            code="missing_canonical",
            category="canonicalization",
            severity="medium",
            status="verified",
            issue="部分 HTML 页面缺少 canonical",
            evidence=missing_canonical[:20],
            action="为唯一、可索引页面设置与最终规范 URL 一致的自引用 canonical。",
            verification="检查原始 HTML 和渲染 DOM 中的 canonical。",
        )

    external_canonical = [
        {"url": page["url"], "canonical": page["canonical"]}
        for page in scope["external_canonical_pages"]
        if page.get("canonical")
    ]
    if external_canonical:
        add_finding(
            findings,
            code="external_canonical",
            category="canonicalization",
            severity="high",
            status="verified",
            issue="页面 canonical 指向其他域名",
            evidence=external_canonical[:20],
            action="确认跨域规范化是否有意；若无，改为本域规范 URL。",
            verification="重新抓取并确认 canonical、sitemap 与最终 URL 对齐。",
        )

    h1_issues = [{"url": page["url"], "h1_count": page.get("h1_count", 0)} for page in html_pages if page.get("h1_count") != 1]
    if h1_issues:
        add_finding(
            findings,
            code="h1_structure",
            category="on_page",
            severity="medium",
            status="verified",
            issue="部分页面没有清晰的单一 H1",
            evidence=h1_issues[:20],
            action="让页面主标题使用一个与搜索意图一致的 H1；其他层级使用 H2/H3。",
            verification="检查渲染 DOM 的标题层级。",
        )

    missing_lang = [page["url"] for page in html_pages if not page.get("html_lang")]
    if missing_lang:
        add_finding(
            findings,
            code="missing_html_lang",
            category="international_seo",
            severity="medium",
            status="verified",
            issue="部分页面缺少 html lang 语言声明",
            evidence=missing_lang[:20],
            action="在每个页面的 html 元素上设置准确的 BCP 47 语言标签，例如 zh-CN 或 en。",
            verification="检查原始 HTML 与渲染 DOM，确认 lang 与页面主要语言一致。",
        )

    missing_alt = [
        {"url": page["url"], "images_missing_alt_attribute": page.get("images_missing_alt_attribute", 0)}
        for page in html_pages
        if page.get("images_missing_alt_attribute", 0) > 0
    ]
    if missing_alt:
        add_finding(
            findings,
            code="images_missing_alt",
            category="on_page",
            severity="low",
            status="verified",
            issue="部分图片缺少 alt 属性",
            evidence=missing_alt[:20],
            action="为承载信息的图片补充简洁、上下文相关的 alt；装饰图片使用空 alt，避免关键词堆砌。",
            verification="检查渲染 DOM，确认所有 img 均有符合用途的 alt 属性。",
        )

    for field, code, label in (("title", "duplicate_title", "title"), ("meta_description", "duplicate_description", "description")):
        groups: dict[str, list[str]] = {}
        for page in html_pages:
            value = page.get(field, "").strip()
            if value:
                groups.setdefault(value, []).append(scope["identity_by_page_id"][id(page)])
        duplicates = [{label: value, "urls": urls[:10]} for value, urls in groups.items() if len(urls) > 1]
        if duplicates:
            add_finding(
                findings,
                code=code,
                category="on_page",
                severity="medium",
                status="verified",
                issue=f"站内存在重复 {label}",
                evidence=duplicates[:10],
                action=f"按页面搜索意图重写唯一 {label}，不要只替换品牌后缀。",
                verification=f"重新抓取并按规范化后的 {label} 分组，确认无非预期重复。",
            )

    invalid_json_ld = [
        {"url": page["url"], "errors": page.get("json_ld_static_errors")}
        for page in html_pages
        if page.get("json_ld_static_errors")
    ]
    if invalid_json_ld:
        add_finding(
            findings,
            code="invalid_static_json_ld",
            category="structured_data",
            severity="medium",
            status="verified",
            issue="静态 HTML 中存在无法解析的 JSON-LD",
            evidence=invalid_json_ld[:20],
            action="修复 JSON 语法，并确保字段与页面可见内容一致。",
            verification="通过 JSON 解析器和 Rich Results Test 复核。",
        )

    no_static_json_ld = [page["url"] for page in html_pages if page.get("json_ld_static_count", 0) == 0]
    if no_static_json_ld:
        add_finding(
            findings,
            code="schema_render_check",
            category="structured_data",
            severity="info",
            status="render_required",
            issue="部分页面的静态 HTML 未发现 JSON-LD，需渲染复核",
            evidence=no_static_json_ld[:20],
            action="使用浏览器读取渲染后的 application/ld+json；仅在仍为空时评估是否缺失。",
            verification="保存渲染 DOM 或 Rich Results Test 结果。",
        )

    pages_by_url = scope["lookup"]
    identity_by_page_id = scope["identity_by_page_id"]
    indexable_page_ids = scope["indexable_page_ids"]
    self_missing: list[str] = []
    reciprocal_missing: list[dict[str, str]] = []
    invalid_targets: list[dict[str, str]] = []
    for page in html_pages:
        alternates = page.get("hreflang", [])
        if not alternates:
            continue
        source = identity_by_page_id[id(page)]
        if source not in {item["url"] for item in alternates}:
            self_missing.append(page["url"])
        for alternate in alternates:
            alternate_url = normalized_url(alternate["url"])
            target = pages_by_url.get(alternate_url)
            if not target:
                continue
            target_identity = identity_by_page_id.get(id(target))
            if id(target) not in indexable_page_ids or target_identity != alternate_url:
                invalid_targets.append(
                    {"from": source, "to": alternate_url, "lang": alternate["lang"]}
                )
                continue
            if source not in {
                normalized_url(item["url"])
                for item in target.get("hreflang", [])
            }:
                reciprocal_missing.append({"from": source, "to": alternate["url"], "lang": alternate["lang"]})
    if self_missing or reciprocal_missing or invalid_targets:
        add_finding(
            findings,
            code="hreflang_consistency",
            category="international_seo",
            severity="high" if reciprocal_missing or invalid_targets else "medium",
            status="verified",
            issue="Hreflang 自引用或互惠关系不完整",
            evidence={
                "self_missing": self_missing[:20],
                "reciprocal_missing": reciprocal_missing[:20],
                "invalid_targets": invalid_targets[:20],
            },
            action="按完整语言集补齐自引用与返回链接，并确保目标 200、可索引、canonical 一致。",
            verification="按 pathname 和规范 URL 重新构建 hreflang 图并检查双向边。",
        )

    blocked_bots = [
        {"category": category, "bot": name}
        for category, policies in audit["discovery"]["robots_ai_bot_access"].items()
        for name, allowed in policies.items()
        if allowed is False
    ]
    if blocked_bots:
        add_finding(
            findings,
            code="ai_bot_policy",
            category="geo",
            severity="low",
            status="verified",
            issue="部分 AI/搜索爬虫被 robots.txt 阻止",
            evidence=blocked_bots,
            action="结合隐私、训练和引用策略确认是否有意；只有希望被相应服务访问时才调整。",
            verification="使用各 User-Agent 重新解析 robots.txt，并记录策略决定。",
        )

    missing_assets = [path for path, item in audit["discovery"]["machine_assets"].items() if item.get("status") != 200]
    if missing_assets:
        add_finding(
            findings,
            code="optional_machine_assets",
            category="geo",
            severity="info",
            status="verified",
            issue="部分可选机器可读资源不可用",
            evidence=missing_assets,
            action="仅在能持续维护准确内容时补充；不要把这些文件当作 Google 排名必要条件。",
            verification="请求资源并确认 200、内容准确、可公开访问。",
        )

    add_finding(
        findings,
        code="core_web_vitals_data",
        category="performance",
        severity="info",
        status="external_data_required",
        issue="Core Web Vitals 未由本次 HTTP 抓取验证",
        evidence="需要 CrUX、PageSpeed 字段数据或 GSC Core Web Vitals。",
        action="获取 LCP、INP、CLS 字段数据并按页面类型和设备分析。",
        verification="保存数据源、时间窗、样本量和通过率。",
    )
    add_finding(
        findings,
        code="answer_engine_visibility_data",
        category="geo",
        severity="info",
        status="external_data_required",
        issue="真实答案引擎品牌提及与域名引用未验证",
        evidence="本脚本不调用 ChatGPT、Perplexity、Claude、Gemini 或 Copilot。",
        action="在用户授权后，对优先查询执行带时间、语言和地区的真实探测。",
        verification="保存逐查询结果、引用 URL、竞争来源和复测日期。",
    )
    return findings


def build_strengths(audit: dict[str, Any], scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    strengths: list[dict[str, Any]] = []
    scope = scope or build_page_scope(audit)
    html_pages = scope["analysis_pages"]
    identity_by_page_id = scope["identity_by_page_id"]
    finding_codes = {item["code"] for item in audit["findings"]}

    if urlsplit(audit["meta"]["target"]).scheme == "https":
        add_strength(
            strengths,
            code="https_enabled",
            category="technical_seo",
            title="目标站点使用 HTTPS",
            evidence=audit["meta"]["target"],
            value="为抓取、用户信任和安全传输提供基础保障。",
        )

    robots = audit["discovery"]["robots"]
    if robots.get("status") == 200:
        add_strength(
            strengths,
            code="robots_available",
            category="crawlability",
            title="robots.txt 可正常读取",
            evidence={"url": robots.get("final_url") or robots.get("requested_url"), "status": 200},
            value="搜索与答案引擎可以读取站点公开抓取策略。",
        )

    valid_sitemaps = [
        {"url": item["url"], "kind": item["kind"], "url_count": item["url_count"]}
        for item in audit["discovery"]["sitemaps"]
        if item.get("status") == 200 and item.get("kind") in {"urlset", "sitemapindex"}
    ]
    if valid_sitemaps:
        add_strength(
            strengths,
            code="sitemap_available",
            category="crawlability",
            title="已提供可解析的 XML Sitemap",
            evidence=valid_sitemaps,
            value="为搜索引擎发现规范 URL 和理解站点规模提供稳定入口。",
        )

    if html_pages and all(not page.get("noindex") for page in html_pages):
        add_strength(
            strengths,
            code="sample_pages_indexable",
            category="indexation",
            title="已抓取 HTML 样本未发现 noindex",
            evidence={"checked_pages": len(html_pages)},
            value="当前样本没有通过页面级指令主动排除搜索收录。",
        )

    if html_pages and all(page.get("title") for page in html_pages):
        add_strength(
            strengths,
            code="titles_present",
            category="on_page",
            title="已抓取页面均具备 title",
            evidence={"covered_pages": len(html_pages)},
            value="为搜索结果理解页面主题提供基础信号。",
        )

    if html_pages and all(page.get("meta_description") for page in html_pages):
        add_strength(
            strengths,
            code="descriptions_present",
            category="on_page",
            title="已抓取页面均具备 meta description",
            evidence={"covered_pages": len(html_pages)},
            value="为搜索摘要和页面价值表达提供可复用文本。",
        )

    self_canonical_pages = [
        identity_by_page_id[id(page)]
        for page in html_pages
        if page.get("canonical")
        and normalized_url(page["canonical"]) == normalized_url(page.get("final_url") or page["url"])
    ]
    if html_pages and len(self_canonical_pages) == len(html_pages):
        add_strength(
            strengths,
            code="self_canonical_complete",
            category="canonicalization",
            title="已抓取页面均设置自引用 canonical",
            evidence={"covered_pages": len(self_canonical_pages)},
            value="帮助搜索引擎聚合重复 URL 信号并识别规范版本。",
        )

    if html_pages and all(page.get("h1_count") == 1 for page in html_pages):
        add_strength(
            strengths,
            code="h1_structure_complete",
            category="on_page",
            title="已抓取页面均具备单一 H1",
            evidence={"covered_pages": len(html_pages)},
            value="页面主主题层级清晰，便于用户和机器理解。",
        )

    if html_pages and all(page.get("html_lang") for page in html_pages):
        languages = sorted({page["html_lang"] for page in html_pages})
        add_strength(
            strengths,
            code="html_lang_present",
            category="international_seo",
            title="已抓取页面均声明主要语言",
            evidence={"covered_pages": len(html_pages), "languages": languages},
            value="帮助搜索、辅助技术和答案引擎正确识别内容语言。",
        )

    valid_json_ld_count = sum(page.get("json_ld_static_valid_count", 0) for page in html_pages)
    if valid_json_ld_count:
        add_strength(
            strengths,
            code="valid_static_json_ld",
            category="structured_data",
            title="静态 HTML 中发现可解析的 JSON-LD",
            evidence={"valid_blocks": valid_json_ld_count, "pages_with_json_ld": sum(1 for page in html_pages if page.get("json_ld_static_valid_count", 0))},
            value="为机器理解实体、页面类型和内容关系提供结构化基础。",
        )

    hreflang_pages = [page for page in html_pages if page.get("hreflang")]
    if hreflang_pages and "hreflang_consistency" not in finding_codes:
        add_strength(
            strengths,
            code="hreflang_consistent",
            category="international_seo",
            title="已抓取的 hreflang 关系通过一致性检查",
            evidence={"pages_with_hreflang": len(hreflang_pages)},
            value="为多语言或多地区页面建立明确的替代关系。",
        )

    author_pages = [page["url"] for page in html_pages if page.get("author_signal")]
    if author_pages:
        add_strength(
            strengths,
            code="author_signals_present",
            category="geo",
            title="部分页面具备作者或署名信号",
            evidence={"pages": author_pages[:20], "count": len(author_pages)},
            value="有助于表达内容责任主体、专业性和可引用来源。",
        )

    allowed_bots = [
        {"category": category, "bot": name}
        for category, policies in audit["discovery"]["robots_ai_bot_access"].items()
        for name, allowed in policies.items()
        if allowed is True
    ]
    if allowed_bots:
        add_strength(
            strengths,
            code="ai_bot_access_available",
            category="geo",
            title=f"{len(allowed_bots)} 个已检查的搜索/AI 爬虫允许访问首页",
            evidence=allowed_bots,
            value="在 robots 策略层面为相应搜索或答案引擎发现公开内容保留入口。",
        )

    available_assets = [path for path, item in audit["discovery"]["machine_assets"].items() if item.get("status") == 200]
    if available_assets:
        add_strength(
            strengths,
            code="machine_assets_available",
            category="geo",
            title="已提供部分机器可读资源",
            evidence=available_assets,
            value="可增强非 Google 答案引擎和代理对公开信息的读取效率。",
        )

    return strengths


def build_recommendations(audit: dict[str, Any]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    findings = audit["findings"]
    blocking = [item for item in findings if item["severity"] in {"critical", "high"} and item["status"] == "verified"]
    verified = [item for item in findings if item["status"] == "verified" and item["severity"] in {"medium", "low"}]
    render_items = [item for item in findings if item["status"] == "render_required"]
    external_items = [item for item in findings if item["status"] == "external_data_required"]

    if blocking:
        recommendations.append(
            {
                "priority": "P0",
                "title": "先处理阻断抓取、索引和规范化的高优先级问题",
                "reason": f"本次发现 {len(blocking)} 项已经验证的高优先级问题。",
                "next_step": "按报告顺序逐项修复，每项都保留变更前证据、最小代码修改和验收结果。",
            }
        )
    if verified:
        recommendations.append(
            {
                "priority": "P1",
                "title": "批量治理已验证的页面级基础问题",
                "reason": f"仍有 {len(verified)} 项中低优先级问题会影响页面理解、摘要质量或可访问性。",
                "next_step": "优先修复共用模板，再抽样复查不同页面类型，避免逐页手工修改产生漂移。",
            }
        )
    if render_items:
        recommendations.append(
            {
                "priority": "P1",
                "title": "补充浏览器渲染证据",
                "reason": f"有 {len(render_items)} 项无法通过静态 HTTP 抓取下结论。",
                "next_step": "抽查首页、列表页、详情页及每种主要语言，保存渲染 DOM 和结构化数据验证结果。",
            }
        )
    if external_items:
        recommendations.append(
            {
                "priority": "P1",
                "title": "建立性能与答案引擎可见性基线",
                "reason": f"有 {len(external_items)} 项需要 GSC、CrUX、PageSpeed 或真实答案引擎结果。",
                "next_step": "记录数据源、时间窗、设备、地区和查询词，避免把实验室数据或模拟回答当作真实表现。",
            }
        )
    recommendations.append(
        {
            "priority": "P2",
            "title": "把巡检加入发布验收和定期回归",
            "reason": "一次性报告无法发现后续模板、路由、robots 或 sitemap 的回归。",
            "next_step": "在发布前后对同一 URL 集合运行巡检，保存 JSON 差异，并为新增高优先级问题设置阻断门槛。",
        }
    )
    return recommendations


def build_score(audit: dict[str, Any]) -> dict[str, Any]:
    penalties = {"critical": 25, "high": 15, "medium": 7, "low": 3, "info": 0}
    verified_findings = [item for item in audit["findings"] if item["status"] == "verified"]
    pending_items = [item for item in audit["findings"] if item["status"] != "verified"]
    deductions = [
        {
            "finding_id": item["id"],
            "severity": item["severity"],
            "points": penalties[item["severity"]],
            "issue": item["issue"],
        }
        for item in verified_findings
        if penalties[item["severity"]] > 0
    ]
    overall = max(0, 100 - sum(item["points"] for item in deductions))
    evidence_items = len(audit["strengths"]) + len(verified_findings)
    evidence_total = evidence_items + len(pending_items)
    evidence_coverage = round(evidence_items * 100 / evidence_total) if evidence_total else 0

    if overall >= 90:
        label = "基础扎实"
        summary = "网站的基础做得不错。接下来补齐细节和待验证数据，就能更稳地提升搜索与答案引擎可见性。"
    elif overall >= 75:
        label = "整体良好"
        summary = "网站具备可用基础，但还有几处会拖慢收录或影响页面理解的问题，按扣分项逐个处理即可。"
    elif overall >= 60:
        label = "需要优化"
        summary = "当前有多项基础问题正在影响抓取、收录或内容理解，建议先处理扣分最高的项目。"
    else:
        label = "优先修复"
        summary = "目前的基础问题较集中，可能明显影响搜索流量。先修复严重和高优先级问题，再补做其他优化。"

    return {
        "version": "1.0",
        "overall": overall,
        "label": label,
        "summary": summary,
        "evidence_coverage": evidence_coverage,
        "verified_finding_count": len(verified_findings),
        "pending_count": len(pending_items),
        "deductions": deductions,
        "pending_items": [
            {"finding_id": item["id"], "status": item["status"], "issue": item["issue"]}
            for item in pending_items
        ],
        "method": "满分 100，最低 0；按问题项扣分，仅计算 verified：严重 25、高 15、中 7、低 3、信息 0。待渲染或待外部数据项目不扣分。本分数用于安排修复优先级，不代表搜索排名或流量预测。",
    }


def compact_evidence(value: Any, limit: int = 1200) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":")) if not isinstance(value, str) else value
    return text if len(text) <= limit else f"{text[:limit]}…（证据已截断，请查看完整 JSON 报告）"


def build_agent_prompts(audit: dict[str, Any]) -> list[dict[str, str]]:
    profiles = (
        {
            "id": "codex",
            "name": "Codex",
            "website": "https://openai.com/codex/",
            "guidance": "先读取仓库中的 AGENTS.md 和项目说明，检查当前工作树，再以最小差异实现修复；运行现有测试并报告命令证据。",
        },
        {
            "id": "openclaw",
            "name": "OpenClaw",
            "website": "https://openclaw.ai/",
            "guidance": "将任务拆成可回滚的受控步骤，只在明确工作区内读写；涉及生产发布、账号或站长平台时先请求人工确认。",
        },
        {
            "id": "hermes",
            "name": "Hermes Agent",
            "website": "https://hermes-agent.nousresearch.com/",
            "guidance": "使用计划、记忆和技能循环逐项执行；可沉淀复用流程，但不得把未经验证的假设写成已完成修复。",
        },
        {
            "id": "claude-code",
            "name": "Claude Code",
            "website": "https://claude.com/product/claude-code",
            "guidance": "先读取 CLAUDE.md、AGENTS.md 和现有测试约定，保持修改聚焦；完成后用测试、构建和页面证据复核。",
        },
    )

    strength_lines = [
        f"- {item['id']} [{item['category']}] {item['title']}；必须保留。证据：{compact_evidence(item['evidence'], 500)}"
        for item in audit["strengths"]
    ] or ["- 本次样本尚未形成可确认的优势项；修改前先建立当前基线。"]
    finding_lines: list[str] = []
    for item in audit["findings"]:
        finding_lines.extend(
            [
                f"- {item['id']} [{item['severity'].upper()} / {item['status']}] {item['issue']}",
                f"  当前证据：{compact_evidence(item['evidence'])}",
                f"  解决方案：{item['action']}",
                f"  验收方法：{item['verification']}",
            ]
        )

    prompts: list[dict[str, str]] = []
    for profile in profiles:
        score = audit["score"]
        lines = [
            f"你是 {profile['name']}，请在目标网站的源代码仓库中执行以下 SEO/GEO 修复任务。",
            "",
            "## 任务上下文",
            f"- 目标站点：{audit['meta']['target']}",
            f"- 巡检完成时间：{audit['meta']['finished_at']}",
            f"- 样本范围：{audit['summary']['pages_crawled']} 个页面，其中 {audit['summary']['html_pages']} 个 HTML 页面",
            f"- 结果评估：{score['overall']}/100（{score['label']}），证据覆盖率 {score['evidence_coverage']}%。评分只用于安排优先级，不替代逐项验收。",
            "- 工作目录：由执行者在开始前确认，不要猜测仓库路径。",
            "",
            "## 执行方式",
            profile["guidance"],
            "",
            "## 强制边界",
            "1. 先复现报告问题并读取相关代码，再修改；不要顺手重构无关模块。",
            "2. verified 项可进入修复；render_required 项必须先用浏览器渲染验证；external_data_required 项必须先取得真实外部数据。",
            "3. 不登录生产后台、不提交站长平台、不更改生产数据，除非用户另行明确授权。",
            "4. 不写入或回显 API Key、Cookie、密码和其他敏感信息。",
            "5. 保留下列已经具备的 SEO/GEO 能力，修复不能造成回归。",
            "",
            "## 已具备且必须保留",
            *strength_lines,
            "",
            "## 问题、解决方案与验收",
            *finding_lines,
            "",
            "## 交付要求",
            "- 输出实际修改文件清单，以及每个修改对应的报告问题 ID。",
            "- 输出运行过的测试、构建、抓取或浏览器验证命令与结果。",
            "- 对无法完成的项目说明阻塞原因和所需输入，不得声称已修复。",
            "- 最后重新运行巡检，对比修复前后 strengths、findings 和未验证项。",
        ]
        prompts.append({**profile, "prompt": "\n".join(lines)})
    return prompts


def audit_site(
    url: str,
    *,
    max_pages: int = 300,
    timeout: float = 10,
    delay: float = 0.1,
    max_bytes: int = 5_000_000,
    max_sitemaps: int = 10,
    max_redirects: int = 5,
    user_agent: str = DEFAULT_USER_AGENT,
    allow_private: bool = False,
    total_timeout: float | None = None,
    should_cancel: Callable[[], bool] | None = None,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    timeout = validate_request_timeout(timeout)
    max_redirects = validate_max_redirects(max_redirects)
    started_at = utc_now()
    deadline = time.monotonic() + total_timeout if total_timeout is not None else None

    def check_control() -> float | None:
        if should_cancel and should_cancel():
            raise AuditCancelledError("Audit cancelled")
        if deadline is None:
            return None
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AuditTimeoutError("Audit exceeded total time limit")
        return remaining

    check_control()
    validate_url_structure(url)
    start_url = normalized_url(url)
    site_origin = origin_for(start_url)
    fetch_options = {
        "timeout": timeout,
        "max_bytes": max_bytes,
        "user_agent": user_agent,
        "allow_private": allow_private,
        "max_redirects": max_redirects,
        "check_control": check_control,
    }

    robots_url = f"{site_origin}/robots.txt"
    robots_meta, robots_text = fetch_url(robots_url, **fetch_options)
    robots_parser: RobotFileParser | None = None
    if robots_meta.get("status") == 200:
        robots_parser = RobotFileParser()
        robots_parser.set_url(robots_url)
        robots_parser.parse(robots_text.splitlines())
    sitemap_candidates = re.findall(r"(?im)^\s*Sitemap:\s*(\S+)", robots_text)
    if not sitemap_candidates:
        sitemap_candidates = [f"{site_origin}/sitemap.xml"]

    sitemap_records: list[dict[str, Any]] = []
    sitemap_urls_raw: list[str] = []
    pending_sitemaps = deque(normalized_url(urljoin(site_origin, item)) for item in sitemap_candidates)
    seen_sitemaps: set[str] = set()
    while pending_sitemaps and len(seen_sitemaps) < max_sitemaps:
        sitemap_url = pending_sitemaps.popleft()
        if sitemap_url in seen_sitemaps or not same_origin(start_url, sitemap_url):
            continue
        seen_sitemaps.add(sitemap_url)
        meta, text = fetch_url(sitemap_url, **fetch_options)
        record = {"url": sitemap_url, "status": meta.get("status"), "error": meta.get("error"), "kind": None, "url_count": 0}
        if meta.get("status") == 200:
            try:
                kind, locations = parse_sitemap(text)
                record["kind"] = kind
                record["url_count"] = len(locations)
                if kind == "sitemapindex":
                    pending_sitemaps.extend(normalized_url(urljoin(sitemap_url, item)) for item in locations)
                else:
                    sitemap_urls_raw.extend(normalized_url(urljoin(sitemap_url, item)) for item in locations)
            except ET.ParseError as exc:
                record["error"] = f"XML parse error: {exc}"
        sitemap_records.append(record)

    sitemap_counter = Counter(sitemap_urls_raw)
    sitemap_duplicate_urls = [url for url, count in sitemap_counter.items() if count > 1]
    sitemap_urls = list(dict.fromkeys(item for item in sitemap_urls_raw if same_origin(start_url, item)))

    machine_assets: dict[str, dict[str, Any]] = {}
    for path in MACHINE_ASSETS:
        meta, _ = fetch_url(f"{site_origin}{path}", **fetch_options)
        machine_assets[path] = {
            "status": meta.get("status"),
            "content_type": meta.get("content_type"),
            "error": meta.get("error"),
        }

    queue = deque([start_url, *sitemap_urls])
    queued = set(queue)
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    while queue and len(pages) < max_pages:
        check_control()
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        if robots_parser and not robots_parser.can_fetch(user_agent, current):
            pages.append({"url": current, "status": None, "error": "Blocked by robots.txt", "blocked_by_robots": True, "is_html": False})
            if on_progress:
                on_progress(
                    {
                        "phase": "crawl",
                        "pages_processed": len(pages),
                        "max_pages": max_pages,
                        "current_url": current,
                    }
                )
            check_control()
            continue
        meta, text = fetch_url(current, **fetch_options)
        page: dict[str, Any] = {
            "url": current,
            "final_url": meta.get("final_url"),
            "status": meta.get("status"),
            "content_type": meta.get("content_type"),
            "elapsed_ms": meta.get("elapsed_ms"),
            "redirects": meta.get("redirects", []),
            "error": meta.get("error"),
            "truncated": meta.get("truncated", False),
            "in_sitemap": current in sitemap_counter,
        }
        content_type = (meta.get("content_type") or "").lower()
        page["is_html"] = meta.get("status") == 200 and content_type in {"text/html", "application/xhtml+xml"}
        if page["is_html"]:
            html_data, links = parse_html(meta.get("final_url") or current, text)
            page.update(html_data)
            for link in links:
                if link not in queued and link not in visited and same_origin(start_url, link):
                    queued.add(link)
                    queue.append(link)
        pages.append(page)
        if on_progress:
            on_progress(
                {
                    "phase": "crawl",
                    "pages_processed": len(pages),
                    "max_pages": max_pages,
                    "current_url": current,
                }
            )
        check_control()
        if delay:
            controlled_sleep(delay, check_control)

    robots_ai_bot_access = {
        category: {
            bot: robots_parser.can_fetch(bot, start_url) if robots_parser else None
            for bot in bots
        }
        for category, bots in AI_BOTS.items()
    }
    audit: dict[str, Any] = {
        "meta": {
            "target": start_url,
            "engine_version": ENGINE_VERSION,
            "started_at": started_at,
            "finished_at": utc_now(),
            "user_agent": user_agent,
            "max_pages": max_pages,
            "allow_private": allow_private,
            "limitations": [
                "Static HTML only; client-rendered metadata and JSON-LD require browser verification.",
                "HTTP timing is not Core Web Vitals.",
                "No Search Console, analytics, backlink, ranking, or answer-engine data is collected.",
            ],
        },
        "discovery": {
            "robots": {**robots_meta, "body": None},
            "robots_ai_bot_access": robots_ai_bot_access,
            "sitemaps": sitemap_records,
            "sitemap_urls": sitemap_urls,
            "sitemap_url_count": len(sitemap_urls_raw),
            "sitemap_unique_url_count": len(set(sitemap_urls_raw)),
            "sitemap_duplicate_url_count": len(sitemap_duplicate_urls),
            "sitemap_duplicate_urls": sitemap_duplicate_urls,
            "machine_assets": machine_assets,
        },
        "pages": pages,
    }
    audit["summary"] = {
        "pages_crawled": len(pages),
        "html_pages": sum(1 for page in pages if page.get("is_html")),
        "failed_pages": sum(1 for page in pages if page.get("status") is None or int(page["status"]) >= 400),
        "robots_blocked_pages": sum(1 for page in pages if page.get("blocked_by_robots")),
        "crawl_limit_reached": len(pages) >= max_pages and bool(queue),
    }
    page_scope = build_page_scope(audit)
    audit["summary"]["analysis_scope"] = page_scope["summary"]
    audit["findings"] = build_findings(audit, page_scope)
    audit["strengths"] = build_strengths(audit, page_scope)
    audit["recommendations"] = build_recommendations(audit)
    audit["score"] = build_score(audit)
    audit["agent_prompts"] = build_agent_prompts(audit)
    severity_counts = Counter(item["severity"] for item in audit["findings"])
    audit["summary"]["finding_counts"] = dict(severity_counts)
    audit["summary"]["strength_count"] = len(audit["strengths"])
    audit["summary"]["recommendation_count"] = len(audit["recommendations"])
    check_control()
    return audit


def markdown_report(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# SEO/GEO 巡检报告",
        "",
        "## 执行摘要",
        "",
        f"- 目标站点：{audit['meta']['target']}",
        f"- 引擎版本：{audit['meta']['engine_version']}",
        f"- 开始时间：{audit['meta']['started_at']}",
        f"- 完成时间：{audit['meta']['finished_at']}",
        f"- 抓取页面：{summary['pages_crawled']}（HTML {summary['html_pages']}）",
        f"- 规范分析页：{summary.get('analysis_scope', {}).get('canonical_indexable_pages', 0)}（排除重定向别名 {summary.get('analysis_scope', {}).get('redirect_aliases_excluded', 0)}、noindex {summary.get('analysis_scope', {}).get('noindex_excluded', 0)}、非规范 canonical {summary.get('analysis_scope', {}).get('canonical_away_excluded', 0)}）",
        f"- 失败页面：{summary['failed_pages']}",
        f"- 达到抓取上限：{'是' if summary['crawl_limit_reached'] else '否'}",
        f"- 已验证优势：{len(audit['strengths'])}",
        f"- 问题与待取证项：{len(audit['findings'])}",
        "",
    ]
    score = audit["score"]
    lines.extend(
        [
            "## 结果评估",
            "",
            f"- 总分：{score['overall']}/100（{score['label']}）",
            f"- 证据覆盖率：{score['evidence_coverage']}%",
            f"- 已验证问题：{score['verified_finding_count']} 项",
            f"- 待补证据：{score['pending_count']} 项（不计入扣分）",
            f"- 评估结论：{score['summary']}",
            f"- 评分方法：{score['method']}",
            "",
            "### 扣分依据",
            "",
        ]
    )
    if score["deductions"]:
        lines.extend(
            f"- {item['finding_id']}：-{item['points']} 分，{item['issue']}"
            for item in score["deductions"]
        )
    else:
        lines.append("- 本次没有需要扣分的已验证问题。")
    lines.extend(["", "### 待补证据", ""])
    if score["pending_items"]:
        lines.extend(
            f"- {item['finding_id']} [{item['status']}]：{item['issue']}"
            for item in score["pending_items"]
        )
    else:
        lines.append("- 本次没有待补证据项目。")
    lines.extend(
        [
            "",
            "## 已经具备的 SEO/GEO 相关内容",
            "",
            "> 以下优势仅代表本次已抓取样本和当前公开证据，后续修改必须避免造成回归。",
            "",
        ]
    )
    if not audit["strengths"]:
        lines.extend(["本次样本尚未形成可确认的优势项。", ""])
    for item in audit["strengths"]:
        evidence = json.dumps(item["evidence"], ensure_ascii=False, indent=2)
        lines.extend(
            [
                f"### {item['id']} {item['title']}",
                "",
                f"- 类别：{item['category']}",
                f"- 状态：{item['status']}",
                f"- 价值：{item['value']}",
                "- 证据：",
                "",
                "```json",
                evidence,
                "```",
                "",
            ]
        )

    lines.extend(["## 存在的问题与针对性解决方案", ""])
    for item in audit["findings"]:
        evidence = json.dumps(item["evidence"], ensure_ascii=False, indent=2)
        lines.extend(
            [
                f"### {item['id']} [{item['severity'].upper()}] {item['issue']}",
                "",
                f"- 类别：{item['category']}",
                f"- 状态：{item['status']}",
                f"- 解决方案：{item['action']}",
                f"- 验收方法：{item['verification']}",
                "- 当前证据：",
                "",
                "```json",
                evidence,
                "```",
                "",
            ]
        )

    lines.extend(["## 建议的后续优化", ""])
    for item in audit["recommendations"]:
        lines.extend(
            [
                f"### {item['priority']} {item['title']}",
                "",
                f"- 原因：{item['reason']}",
                f"- 下一步：{item['next_step']}",
                "",
            ]
        )

    lines.extend(["## 智能体执行提示词", ""])
    for item in audit["agent_prompts"]:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- 官网：{item['website']}",
                "",
                "```text",
                item["prompt"],
                "```",
                "",
            ]
        )

    lines.extend(["## 已抓取页面", "", "| URL | HTTP | 类型 |", "|---|---:|---|"])
    for page in audit["pages"]:
        page_url = str(page.get("url", "")).replace("|", "\\|")
        page_status = page.get("status") if page.get("status") is not None else "-"
        page_type = "HTML" if page.get("is_html") else "非 HTML"
        lines.append(f"| {page_url} | {page_status} | {page_type} |")
    lines.extend([""])

    lines.extend(["## 限制", ""])
    lines.extend(f"- {item}" for item in audit["meta"]["limitations"])
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public site URL, including http:// or https://")
    parser.add_argument("--max-pages", type=int, default=300, help="Maximum same-origin pages to crawl (default: 300)")
    parser.add_argument("--timeout", type=float, default=10, help="Per-request timeout in seconds")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between page requests in seconds")
    parser.add_argument("--max-bytes", type=int, default=5_000_000, help="Maximum response bytes read per URL")
    parser.add_argument("--max-sitemaps", type=int, default=10, help="Maximum sitemap files to inspect")
    parser.add_argument(
        "--max-redirects",
        type=parse_max_redirects,
        default=5,
        help="Maximum redirects per request (default: 5)",
    )
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--allow-private", action="store_true", help="Allow private/loopback targets for explicitly authorized local testing")
    parser.add_argument("--json-out", type=Path, help="Write complete audit JSON to this path")
    parser.add_argument("--markdown-out", type=Path, help="Write Markdown findings to this path")
    parser.add_argument("--html-out", type=Path, help="Write a self-contained HTML report to this path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.max_pages < 1 or args.max_pages > 5000:
        print("--max-pages must be between 1 and 5000", file=sys.stderr)
        return 2
    try:
        audit = audit_site(
            args.url,
            max_pages=args.max_pages,
            timeout=args.timeout,
            delay=max(0, args.delay),
            max_bytes=args.max_bytes,
            max_sitemaps=args.max_sitemaps,
            max_redirects=args.max_redirects,
            user_agent=args.user_agent,
            allow_private=args.allow_private,
        )
    except (AuditCancelledError, AuditTimeoutError, ValueError, OSError) as exc:
        print(f"Audit failed: {exc}", file=sys.stderr)
        return 2

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(markdown_report(audit), encoding="utf-8")
    if args.html_out:
        args.html_out.parent.mkdir(parents=True, exist_ok=True)
        args.html_out.write_text(html_report(audit), encoding="utf-8")

    print(
        json.dumps(
            {
                "target": audit["meta"]["target"],
                "summary": audit["summary"],
                "json_out": str(args.json_out) if args.json_out else None,
                "markdown_out": str(args.markdown_out) if args.markdown_out else None,
                "html_out": str(args.html_out) if args.html_out else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
