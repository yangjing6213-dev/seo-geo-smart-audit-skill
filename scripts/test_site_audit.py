#!/usr/bin/env python3

from email.message import Message
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO, StringIO
import json
from pathlib import Path
import socket
import ssl
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
import urllib.request as urllib_request


TEST_CERT_PEM = """\
-----BEGIN CERTIFICATE-----
MIIC9DCCAdygAwIBAgIUEvtz5zILqq88rn1qxxYe62Mxg8wwDQYJKoZIhvcNAQEL
BQAwGzEZMBcGA1UEAwwQb3JpZ2luYWwuZXhhbXBsZTAeFw0yNTAxMDEwMDAwMDBa
Fw0zNTAxMDEwMDAwMDBaMBsxGTAXBgNVBAMMEG9yaWdpbmFsLmV4YW1wbGUwggEi
MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC3tXZDSf80p7waYQnssRA9QQtW
2aUHDCEeApWLM5SQR/XsXxFBXtoeTHrhjyuOYiikynfjJF3t4hOBZ5Om2x13pivT
sijIDhgiXSbiy+cEoJ1v9Qw6wR913bKJtG/5+7zfqSJ/2o6epVAD842u6MfU09an
SxBvyVbfS7q6VVLoRMyjL2IacIqMN1+Sxwt5iS95ZqUMq+6mzIIQL4XVgQOlkc34
TX8swDMuYacUT/pbC8017NPKLWmYHYHO7zKyAPfh0VnrUXwUKIUpO8P1ZcnqeGUx
4ACy+6Bn2H+skmd7qK6CcCSvVdl9yNv0oy12Ng6U9b9FbYW9mj4RqD7lyn5xAgMB
AAGjMDAuMBsGA1UdEQQUMBKCEG9yaWdpbmFsLmV4YW1wbGUwDwYDVR0TAQH/BAUw
AwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAhRk4Tx0UWtS/6FvDgrzP4FWPJQ9OHEZG
FQopEEUBW3zzdWqr+U2n+jI0R7YyNgNBZ70snEvC12FEZNlM8XTxQ2w+Grys4ZKV
FsTmckErEsUZxcCpM6SshmjN4h2rwesjvDXI6VRR0TJgD8K3qib9lUCq35+fbqsv
mdTkiE0l56rD8IFB7hzJPBtuVfPXalZxYnxTw5DZwT23i/XIIC+2U/6sjAYxaBKj
lNpiwY7WJ3HDAXEPoK+Jw/F84PRxWALmWbGVukE5tlqKThTCU4o61WWvctxrbGYx
6jon+ho87aKINsStUNC2T1wf41g3rBznT2MgJ3U0Lxe5lakqj14oPA==
-----END CERTIFICATE-----
"""

TEST_KEY_BODY = """\
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC3tXZDSf80p7wa
YQnssRA9QQtW2aUHDCEeApWLM5SQR/XsXxFBXtoeTHrhjyuOYiikynfjJF3t4hOB
Z5Om2x13pivTsijIDhgiXSbiy+cEoJ1v9Qw6wR913bKJtG/5+7zfqSJ/2o6epVAD
842u6MfU09anSxBvyVbfS7q6VVLoRMyjL2IacIqMN1+Sxwt5iS95ZqUMq+6mzIIQ
L4XVgQOlkc34TX8swDMuYacUT/pbC8017NPKLWmYHYHO7zKyAPfh0VnrUXwUKIUp
O8P1ZcnqeGUx4ACy+6Bn2H+skmd7qK6CcCSvVdl9yNv0oy12Ng6U9b9FbYW9mj4R
qD7lyn5xAgMBAAECggEAEXFlZ+uKvnvUBx0s+BBdM7O4A+hpHEuGiXbtWWjts5Vh
la6hJiJ/dgkE/I2/hlFuUoH28tZCej0mZPm/XJnJfnwvWnZmxjgFtUhAUksnWu/K
gxWIB7whOevG8VRJ8uPNgd8UANfGWuyPYGYBD0PYVYOXtLgSjiABOPUpJwVwTdAG
YBN0uO0GiP1ZQt9rGxDvYbooYlcYZRfTiIjjYs+3EBvuii3gzyUZznxsBhBVAbX7
+Js/RrMamLlBItmBe2dMfO64flc686ZD+rt/P60Fo6T7F5CZ8PMnQpinydhBxGsE
hdGZU2PLMpCCYiZcSwbePo0Ifv9YbdiLo3SeB/7CUQKBgQD0IpaWwmOlTOOjBxj3
argHcAVuTsUgjtHObuQ77lM9jG0/vupi7QNUPKE4mpLBGbMXLb9ef/XnH4IyRzca
mW4Ehg+etpGXg37HU9tmqf5LDLEkoKkoI3ZwT/GXSXjOrVAvVwWLvFQHNgwpDLp9
l9X8yMSfpfsDCl0uMGVdh+ugcwKBgQDAoxQ8b4KwAv5K02Zp2xa4IuDFOuDu1VLT
Ne3ScfCJDcZRhkYwgKkHm4paTAgi9KX8IzKQeMyMIePOEn+w/UekQCSuw/uTJ3WX
ZSsTRtcfZPBHkOXSFDhUcaU0h711ngrlRZqTCg3kcwdCnySYjcaJtAgF1y9IueP5
Y9szkQQgiwKBgQCZ+a6sixG50dLIodNXSNGkrzxdpASkUi91WW9NdTS+3vCQgeLm
XcH5wPuV7bedXo4bkljeSypWiQLenxfcCOTgqYT0fwU4YFD3eqYoDBM8VlbrWQEX
Nbafg2xGFKrC/4BROzteNHtyyN3GjiaYy8jE1ANfBZpZApJebVuhL/amjQKBgC7A
JSwZn+zZfR9puKQeEKB1jnkvNeGgke5CW0pEbqzEVAn6/VPOFbeL7wLFCwB4wUO0
wxO+zV2A6AleAfFRNq7NBloHpCltXSN14QNXoOO0mn+z0aKvV5Be2EosWzWNOnWz
87SVrxNvOybW+omvdqx6ravFMmuC+anPqyYTnp3LAoGAOTwVnbx9HHyaaxjsiAKW
+uyeLFscKqsoHSK1JOj91wtSyHaXYeK+LQssmxVgyByjvJLYoEYvP2qX+z4Q30IJ
Nx962Qzm9haPBbrMmxedst4BGNhSJ3GNTF/pXtZHWcUw1vApZp6cVMEbNo4oLuNl
3yp1JQ/GUkDSZrESHwJM2WU=
"""


sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_render import BrowserRendererUnavailableError  # noqa: E402
from html_report import html_report  # noqa: E402
import site_audit as site_audit_module  # noqa: E402
from site_audit import (  # noqa: E402
    AI_BOTS,
    AuditCancelledError,
    AuditHTMLParser,
    AuditTimeoutError,
    PinnedHTTPSConnection,
    audit_site,
    build_findings,
    build_score,
    build_strengths,
    connect_resolved,
    fetch_url,
    markdown_report,
    validate_url,
)


def ipv4_resolver_script(address: str, counter_path: Path | None = None) -> str:
    counter_lines = ""
    if counter_path is not None:
        counter_lines = (
            "from pathlib import Path\n"
            f"counter = Path({str(counter_path)!r})\n"
            "count = int(counter.read_text() or '0') if counter.exists() else 0\n"
            "counter.write_text(str(count + 1))\n"
        )
    return (
        "import json\n"
        "import socket\n"
        "import sys\n"
        f"{counter_lines}"
        "port = int(sys.argv[2])\n"
        f"print(json.dumps([[socket.AF_INET, socket.SOCK_STREAM, "
        f"socket.IPPROTO_TCP, '', [{address!r}, port]]]))\n"
    )


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.server.request_count = getattr(self.server, "request_count", 0) + 1
        if hasattr(self.server, "host_headers"):
            self.server.host_headers.append(self.headers.get("Host"))
        response_delay = getattr(self.server, "response_delay", 0)
        if response_delay:
            time.sleep(response_delay)
        if self.path == "/trickle":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", "64")
            self.end_headers()
            try:
                for _ in range(64):
                    self.wfile.write(b"x")
                    self.wfile.flush()
                    time.sleep(0.01)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            return
        if self.path in {"/stall", "/error-stall"}:
            self.send_response(503 if self.path == "/error-stall" else 200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", "64")
            self.end_headers()
            self.server.stall_started_at = time.monotonic()
            self.server.stall_started.set()
            time.sleep(2)
            try:
                self.wfile.write(b"x")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            return
        if self.path in {"/redirect-start", "/redirect-middle"}:
            location = (
                "/redirect-middle"
                if self.path == "/redirect-start"
                else self.server.redirect_location
            )
            self.send_response(302)
            self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        port = self.server.server_address[1]
        if self.path == "/robots.txt" and getattr(self.server, "robots_missing", False):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"not found")
            return
        robots_body = getattr(
            self.server,
            "robots_body",
            "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",
        )
        routes = {
            "/robots.txt": ("text/plain", robots_body),
            "/sitemap.xml": (
                "application/xml",
                f"<?xml version='1.0'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
                f"<url><loc>http://127.0.0.1:{port}/</loc></url>"
                f"<url><loc>http://127.0.0.1:{port}/about</loc></url>"
                f"<url><loc>http://127.0.0.1:{port}/about</loc></url></urlset>",
            ),
            "/llms.txt": ("text/plain", "# Fixture Site\n"),
            "/": (
                "text/html",
                f"<html lang='zh-CN'><head><title>首页</title>"
                f"<meta name='description' content='测试首页'>"
                f"<link rel='canonical' href='http://127.0.0.1:{port}/'>"
                f"<script type='application/ld+json'>{{\"@type\":\"WebSite\"}}</script>"
                f"</head><body><h1>首页</h1><a href='/about'>关于</a></body></html>",
            ),
            "/about": (
                "text/html",
                f"<html lang='zh-CN'><head><title>关于</title>"
                f"<meta name='description' content='关于我们'>"
                f"<link rel='canonical' href='http://127.0.0.1:{port}/about'>"
                f"</head><body><h1>关于</h1><p>公开测试内容。</p></body></html>",
            ),
        }
        if self.path not in routes:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"not found")
            return
        content_type, body = routes[self.path]
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


class SiteAuditTests(unittest.TestCase):
    def run_fixture_audit(self, **kwargs):
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.request_count = 0
        server.robots_body = kwargs.pop("robots_body", None) or (
            "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n"
        )
        thread = threading.Thread(
            target=lambda: server.serve_forever(poll_interval=0.01),
            daemon=True,
        )
        thread.start()
        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/"
            max_pages = kwargs.pop("max_pages", 5)
            result = audit_site(
                target,
                max_pages=max_pages,
                timeout=2,
                delay=kwargs.pop("delay", 0),
                max_sitemaps=2,
                allow_private=True,
                **kwargs,
            )
            return result, server.request_count
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_html_parser_extracts_core_fields(self) -> None:
        parser = AuditHTMLParser()
        parser.feed(
            "<html lang='en'><head><meta charset='utf-8'><title>Example</title>"
            "<meta name='description' content='Description'>"
            "<script type='application/ld+json'>{\"@type\":\"Article\"}</script>"
            "</head><body><h1>Heading</h1><img src='x.png'></body></html>"
        )
        self.assertEqual("Example", "".join(parser.title_parts))
        self.assertEqual("en", parser.html_lang)
        self.assertEqual(1, parser.images_missing_alt)
        self.assertEqual(1, len(parser.json_ld_blocks))

    def test_bounded_local_audit(self) -> None:
        result, _ = self.run_fixture_audit()
        target = result["meta"]["target"]

        self.assertEqual(2, result["summary"]["html_pages"])
        self.assertEqual("1.4.9", result["meta"].get("engine_version"))
        self.assertEqual(1, result["discovery"]["sitemap_duplicate_url_count"])
        self.assertIn("Static HTML only", result["meta"]["limitations"][0])

    def test_fetch_url_can_return_bytes_and_safe_redirect_for_browser_requests(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.request_count = 0
        server.redirect_location = "/"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_address[1]}"
            redirect_meta, redirect_body = fetch_url(
                f"{origin}/redirect-start",
                timeout=2,
                max_bytes=10_000,
                user_agent="test-agent",
                allow_private=True,
                return_bytes=True,
                follow_redirects=False,
                allowed_origin=origin,
            )
            page_meta, page_body = fetch_url(
                f"{origin}/",
                timeout=2,
                max_bytes=10_000,
                user_agent="test-agent",
                allow_private=True,
                return_bytes=True,
                allowed_origin=origin,
            )

            self.assertEqual(302, redirect_meta["status"])
            self.assertEqual(f"{origin}/redirect-middle", redirect_meta["redirect_url"])
            self.assertEqual(b"", redirect_body)
            self.assertEqual(200, page_meta["status"])
            self.assertEqual("utf-8", page_meta["content_charset"])
            self.assertIsInstance(page_body, bytes)
            self.assertIn("首页".encode("utf-8"), page_body)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_origin_comparison_normalizes_default_ports_and_idn_hosts(self) -> None:
        self.assertTrue(site_audit_module.same_origin("https://example.com:443/a", "https://example.com/b"))
        self.assertTrue(site_audit_module.same_origin("http://例子.测试/a", "http://xn--fsqu00a.xn--0zwm56d/b"))
        self.assertFalse(site_audit_module.same_origin("https://example.com:444/", "https://example.com/"))
        self.assertFalse(site_audit_module.same_origin("http://example.com:0/", "http://example.com/"))
        self.assertFalse(site_audit_module.same_origin("https://example.com:99999/", "https://example.com:99999/"))

    def test_browser_fetcher_rejects_cross_origin_redirect_before_second_resolution(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.request_count = 0
        server.redirect_location = "http://outside.example/private-target"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        local_addresses = socket.getaddrinfo(
            "127.0.0.1",
            server.server_address[1],
            type=socket.SOCK_STREAM,
            flags=socket.AI_NUMERICHOST,
        )
        try:
            origin = f"http://public.example:{server.server_address[1]}"
            with patch.object(
                site_audit_module,
                "resolve_url",
                return_value=tuple(local_addresses),
            ) as resolve_url:
                result, body = fetch_url(
                    f"{origin}/redirect-middle",
                    timeout=2,
                    max_bytes=10_000,
                    user_agent="test-agent",
                    allow_private=True,
                    return_bytes=True,
                    follow_redirects=False,
                    allowed_origin=origin,
                )

            self.assertIsNone(result["status"])
            self.assertEqual("Redirect target validation failed", result["error"])
            self.assertEqual(b"", body)
            self.assertEqual(1, resolve_url.call_count)
            self.assertEqual(1, server.request_count)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_bounded_local_audit_scoring_and_reports(self) -> None:
        result, _ = self.run_fixture_audit()
        target = result["meta"]["target"]
        self.assertEqual(200, result["discovery"]["machine_assets"]["/llms.txt"]["status"])
        self.assertIn("sitemap_duplicate_urls", {item["code"] for item in result["findings"]})

        strength_codes = {item["code"] for item in result["strengths"]}
        self.assertTrue(
            {
                "robots_available",
                "sitemap_available",
                "titles_present",
                "descriptions_present",
                "self_canonical_complete",
                "h1_structure_complete",
                "html_lang_present",
                "valid_static_json_ld",
                "ai_bot_access_available",
                "machine_assets_available",
            }.issubset(strength_codes)
        )

        prompt_ids = {item["id"] for item in result["agent_prompts"]}
        self.assertEqual({"codex", "openclaw", "hermes", "claude-code"}, prompt_ids)
        for item in result["agent_prompts"]:
            self.assertIn(target, item["prompt"])
            self.assertIn("结果评估", item["prompt"])
            self.assertIn("解决方案", item["prompt"])
            self.assertIn("验收方法", item["prompt"])

        score = result["score"]
        self.assertEqual(93, score["overall"])
        self.assertEqual("基础扎实", score["label"])
        self.assertGreater(score["evidence_coverage"], 0)
        self.assertGreater(score["pending_count"], 0)
        self.assertEqual(7, sum(item["points"] for item in score["deductions"]))
        self.assertTrue(any(item["finding_id"] == "F001" for item in score["deductions"]))

        markdown = markdown_report(result)
        self.assertIn("## 结果评估", markdown)
        self.assertIn("总分：93/100", markdown)
        self.assertIn("## 已经具备的 SEO/GEO 相关内容", markdown)
        self.assertIn("## 存在的问题与针对性解决方案", markdown)
        self.assertIn("## 智能体执行提示词", markdown)
        self.assertIn("### Codex", markdown)
        self.assertIn("### Hermes Agent", markdown)

    def test_browser_render_rejects_private_override_before_network_access(self) -> None:
        with (
            self.assertRaisesRegex(ValueError, "only for public targets"),
            patch.object(site_audit_module.subprocess, "Popen") as resolver,
        ):
            audit_site("http://127.0.0.1/", allow_private=True, render_browser=True)
        resolver.assert_not_called()

    def test_missing_browser_setup_fails_before_site_requests(self) -> None:
        with (
            patch(
                "browser_render.ensure_browser_runtime",
                side_effect=BrowserRendererUnavailableError("optional browser setup missing"),
            ),
            patch.object(site_audit_module, "fetch_url") as fetcher,
            self.assertRaises(BrowserRendererUnavailableError),
        ):
            audit_site("https://example.com/", render_browser=True)
        fetcher.assert_not_called()

    def test_browser_mode_explains_that_static_html_still_drives_the_score(self) -> None:
        def fake_fetch(request_url: str, **_kwargs: object) -> tuple[dict[str, object], str]:
            if request_url == "https://example.com/":
                return (
                    {
                        "status": 200,
                        "final_url": request_url,
                        "content_type": "text/html",
                        "error": None,
                        "elapsed_ms": 1,
                    },
                    "<html lang='en'><head><title>Static</title></head><body><h1>Page</h1></body></html>",
                )
            return (
                {
                    "status": 404,
                    "final_url": request_url,
                    "content_type": "text/plain",
                    "error": None,
                    "elapsed_ms": 1,
                },
                "",
            )

        rendering = {
            "enabled": True,
            "eligible_pages": 1,
            "sampled_pages": 1,
            "rendered_pages": 1,
            "failed_pages": 0,
            "blocked_requests": 0,
            "affects_score": False,
            "rendered_html_retained": False,
        }
        with (
            patch("browser_render.ensure_browser_runtime"),
            patch("browser_render.render_browser_pages", return_value=rendering),
            patch.object(site_audit_module, "fetch_url", side_effect=fake_fetch),
        ):
            result = audit_site("https://example.com/", max_pages=1, delay=0, render_browser=True)

        self.assertEqual(rendering, result["browser_rendering"])
        self.assertIn("Base score uses static HTML", result["meta"]["limitations"][0])

    def test_browser_observations_do_not_change_score_and_html_escapes_site_content(self) -> None:
        result, _ = self.run_fixture_audit()
        score_before = build_score(result)
        result["browser_rendering"] = {
            "enabled": True,
            "eligible_pages": 1,
            "sampled_pages": 1,
            "rendered_pages": 1,
            "failed_pages": 0,
            "blocked_requests": 2,
            "affects_score": False,
            "rendered_html_retained": False,
        }
        result["pages"][0]["browser_render"] = {
            "status": "completed",
            "http_status": 200,
            "title": "<script>alert(1)</script>",
            "meta_description": "Rendered description",
            "canonical": "https://example.com/",
            "html_lang": "en",
            "robots_directive": "",
            "h1_count": 1,
            "h1": ["Rendered heading"],
            "json_ld_static_count": 1,
            "json_ld_static_valid_count": 1,
            "differences": ["title", "h1"],
            "error": None,
        }

        self.assertEqual(score_before, build_score(result))
        html = html_report(result)
        markdown = markdown_report(result)
        self.assertIn("浏览器渲染观察", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("浏览器渲染观察（补充证据，不参与评分）", markdown)

    def test_indexability_scope_removes_false_positive_findings(self) -> None:
        result, _ = self.run_fixture_audit()
        base_url = result["meta"]["target"].rstrip("/")

        def page(
            path: str,
            *,
            title: str,
            description: str,
            canonical: str | None = None,
            final_url: str | None = None,
            noindex: bool = False,
            redirects: list[dict[str, object]] | None = None,
            json_ld: bool = True,
            hreflang: list[dict[str, str]] | None = None,
        ) -> dict[str, object]:
            url = f"{base_url}{path}"
            return {
                "url": url,
                "final_url": final_url or url,
                "status": 200,
                "content_type": "text/html",
                "redirects": redirects or [],
                "error": None,
                "truncated": False,
                "in_sitemap": False,
                "is_html": True,
                "title": title,
                "title_length": len(title),
                "meta_description": description,
                "meta_description_length": len(description),
                "canonical": canonical or url,
                "html_lang": "zh-CN",
                "robots_directive": "noindex,follow" if noindex else "index,follow",
                "noindex": noindex,
                "h1_count": 1,
                "h1": [title],
                "h2_count": 0,
                "images_missing_alt_attribute": 0,
                "internal_link_count": 2,
                "external_link_count": 0,
                "hreflang": hreflang or [],
                "json_ld_static_count": 1 if json_ld else 0,
                "json_ld_static_valid_count": 1 if json_ld else 0,
                "json_ld_static_errors": [],
                "word_count": 100,
                "author_signal": False,
            }

        canonical_a = f"{base_url}/canonical-a"
        canonical_b = f"{base_url}/canonical-b"
        parameter_url = f"{base_url}/catalog?sort=popular"
        result["pages"] = [
            page("/canonical-a", title="Shared title", description="Canonical A"),
            page("/canonical-b", title="Shared title", description="Canonical B"),
            page(
                "/old-short",
                title="Shared title",
                description="Canonical A",
                canonical=canonical_a,
                final_url=canonical_a,
                redirects=[{"status": 301, "from": f"{base_url}/old-short", "to": canonical_a}],
            ),
            page("/login", title="Shared title", description="Utility page", noindex=True, json_ld=False),
            page("/search?q=ai", title="Shared title", description="Utility page", noindex=True, json_ld=False),
            page(
                "/catalog?sort=popular",
                title="Catalog filter",
                description="Filtered catalog",
                canonical=f"{base_url}/catalog",
                hreflang=[
                    {"lang": "zh-CN", "url": parameter_url},
                    {"lang": "en", "url": f"{base_url}/en/catalog"},
                ],
            ),
            page("/en/catalog", title="English catalog", description="English catalog"),
        ]
        result["discovery"]["sitemap_urls"] = []
        result["discovery"]["sitemap_duplicate_url_count"] = 0
        result["discovery"]["sitemap_duplicate_urls"] = []
        result["findings"] = build_findings(result)
        result["strengths"] = build_strengths(result)
        result["score"] = build_score({**result, "findings": result["findings"], "strengths": result["strengths"]})

        finding_codes = {item["code"] for item in result["findings"]}
        self.assertIn("duplicate_title", finding_codes)
        self.assertNotIn("noindex_pages_review", finding_codes)
        self.assertNotIn("duplicate_description", finding_codes)
        self.assertNotIn("hreflang_consistency", finding_codes)
        self.assertNotIn("schema_render_check", finding_codes)
        duplicate = next(item for item in result["findings"] if item["code"] == "duplicate_title")
        duplicate_urls = set(duplicate["evidence"][0]["urls"])
        self.assertEqual({canonical_a, canonical_b}, duplicate_urls)
        self.assertEqual(93, result["score"]["overall"])
        self.assertEqual(1, len(result["score"]["deductions"]))
        self.assertEqual(duplicate["id"], result["score"]["deductions"][0]["finding_id"])

    def test_indexability_scope_keeps_real_sitemap_noindex_conflict(self) -> None:
        result, _ = self.run_fixture_audit()
        page = dict(result["pages"][0])
        page["noindex"] = True
        page["robots_directive"] = "noindex,follow"
        page["in_sitemap"] = True
        result["pages"] = [page]
        result["discovery"]["sitemap_urls"] = [page["url"]]

        findings = build_findings(result)

        conflict = next(item for item in findings if item["code"] == "sitemap_noindex_conflict")
        self.assertEqual("verified", conflict["status"])
        self.assertNotIn("noindex_pages_review", {item["code"] for item in findings})

    def test_indexability_scope_keeps_real_hreflang_target_issue(self) -> None:
        result, _ = self.run_fixture_audit()
        source = dict(result["pages"][0])
        target = dict(result["pages"][1])
        source["url"] = f"{result['meta']['target'].rstrip('/')}/source"
        source["final_url"] = source["url"]
        source["canonical"] = source["url"]
        target["url"] = f"{result['meta']['target'].rstrip('/')}/target"
        target["final_url"] = target["url"]
        target["canonical"] = target["url"]
        target["noindex"] = True
        target["robots_directive"] = "noindex,follow"
        source["hreflang"] = [{"lang": "en", "url": target["url"]}]
        result["pages"] = [source, target]

        findings = build_findings(result)

        self.assertIn("hreflang_consistency", {item["code"] for item in findings})

    def test_html_report_is_self_contained_accessible_and_escapes_audit_text(self) -> None:
        result, _ = self.run_fixture_audit()
        result["meta"]["target"] = "https://example.com/<script>alert('x')</script>"

        report = html_report(result)

        self.assertTrue(report.lstrip().lower().startswith("<!doctype html>"))
        self.assertIn('<html lang="zh-CN">', report)
        self.assertIn('<meta name="viewport"', report)
        self.assertIn('data-report-version="1.0"', report)
        self.assertIn('id="overview"', report)
        self.assertIn('id="findings"', report)
        self.assertIn('id="strengths"', report)
        self.assertIn('id="recommendations"', report)
        self.assertIn('id="pages"', report)
        self.assertIn('id="methodology"', report)
        self.assertIn("93", report)
        self.assertIn("ENHE AI工作室", report)
        self.assertIn("https://www.enhe-tech.com.cn", report)
        self.assertIn("prefers-reduced-motion: reduce", report)
        self.assertIn('data-filter="all"', report)
        self.assertIn(result["findings"][0]["issue"], report)
        self.assertIn(result["strengths"][0]["title"], report)
        self.assertIn("&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;", report)
        self.assertNotIn("<script>alert('x')</script>", report)
        self.assertNotIn("https://cdn", report)

    def test_evidence_coverage_explains_its_check_item_denominator(self) -> None:
        result, _ = self.run_fixture_audit()

        self.assertIn("全部检查项的比例", result["score"]["method"])
        self.assertIn("不代表页面抓取覆盖", result["score"]["method"])
        self.assertIn("检查证据完备度", markdown_report(result))

    def test_external_evidence_is_summarized_in_reports_and_html_escaped(self) -> None:
        result, _ = self.run_fixture_audit()
        result["external_evidence"] = {
            "search_console": {
                "period_start": "2026-10-01",
                "period_end": "2026-10-14",
                "page_rows": 1,
                "clicks": 2,
                "impressions": 10,
                "ctr_percent": 20.0,
                "average_position": 4.5,
            },
            "answer_engine_samples": [
                {
                    "engine": "<img src=x onerror=alert(1)>",
                    "checked_at": "2026-10-17",
                    "query_samples": 2,
                    "queries_with_site_citation": 1,
                    "citation_rate_percent": 50.0,
                }
            ],
            "affects_score": False,
            "raw_rows_retained": False,
        }

        markdown = markdown_report(result)
        report = html_report(result)

        self.assertIn("外部数据补充（用户导入）", markdown)
        self.assertIn("抽样引用率 50.0%", markdown)
        self.assertIn("Supplemental data", report)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", report)
        self.assertNotIn("<img src=x onerror=alert(1)>", report)

    def test_cli_writes_html_report_and_returns_its_path(self) -> None:
        result, _ = self.run_fixture_audit()

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            json_path = output_directory / "audit.json"
            markdown_path = output_directory / "audit.md"
            html_path = output_directory / "audit.html"
            stdout = StringIO()
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "site_audit.py",
                        "https://example.com",
                        "--json-out",
                        str(json_path),
                        "--markdown-out",
                        str(markdown_path),
                        "--html-out",
                        str(html_path),
                        "--render-browser",
                    ],
                ),
                patch.object(site_audit_module, "audit_site", return_value=result) as audit_site,
                patch.object(sys, "stdout", stdout),
            ):
                exit_code = site_audit_module.main()

            completion = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertEqual(str(html_path), completion["html_out"])
            self.assertTrue(json_path.is_file())
            self.assertTrue(markdown_path.is_file())
            self.assertTrue(html_path.is_file())
            self.assertIn("ENHE AI工作室", html_path.read_text(encoding="utf-8"))
            self.assertTrue(audit_site.call_args.kwargs["render_browser"])

    def test_cli_disallows_private_override_with_browser_rendering(self) -> None:
        stderr = StringIO()
        with (
            patch.object(
                sys,
                "argv",
                ["site_audit.py", "http://127.0.0.1/", "--allow-private", "--render-browser"],
            ),
            patch.object(sys, "stderr", stderr),
            patch.object(site_audit_module.subprocess, "Popen") as resolver,
            patch.object(site_audit_module, "audit_site") as audit_site,
        ):
            exit_code = site_audit_module.main()

        self.assertEqual(2, exit_code)
        self.assertIn("cannot be combined", stderr.getvalue())
        resolver.assert_not_called()
        audit_site.assert_not_called()

    def test_ai_bot_policies_keep_categories_and_each_bot(self) -> None:
        self.assertEqual(
            {
                "search": ("OAI-SearchBot", "PerplexityBot"),
                "training": ("GPTBot", "Google-Extended", "ClaudeBot"),
                "user_fetch": ("ChatGPT-User", "Claude-User"),
            },
            AI_BOTS,
        )
        result, _ = self.run_fixture_audit()
        policies = result["discovery"]["robots_ai_bot_access"]
        self.assertEqual(set(AI_BOTS), set(policies))
        for category, bots in AI_BOTS.items():
            self.assertEqual(set(bots), set(policies[category]))
            for bot in bots:
                self.assertIs(policies[category][bot], True)

    def test_ai_bot_policies_apply_conflicting_rules_per_bot(self) -> None:
        robots_body = """\
User-agent: OAI-SearchBot
Disallow: /

User-agent: PerplexityBot
Allow: /

User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Allow: /

User-agent: ClaudeBot
Disallow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-User
Disallow: /

User-agent: *
Allow: /
Sitemap: /sitemap.xml
"""
        result, _ = self.run_fixture_audit(robots_body=robots_body)
        self.assertEqual(
            {
                "search": {
                    "OAI-SearchBot": False,
                    "PerplexityBot": True,
                },
                "training": {
                    "GPTBot": False,
                    "Google-Extended": True,
                    "ClaudeBot": False,
                },
                "user_fetch": {
                    "ChatGPT-User": True,
                    "Claude-User": False,
                },
            },
            result["discovery"]["robots_ai_bot_access"],
        )

    def test_dns_rebinding_cannot_change_the_actual_connection_target(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.request_count = 0
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def direct_opener(*handlers):
            return urllib_request.build_opener(urllib_request.ProxyHandler({}), *handlers)

        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                counter_path = Path(temporary_directory) / "resolver-count.txt"
                rebinding_script = (
                    "import json\n"
                    "import socket\n"
                    "import sys\n"
                    "from pathlib import Path\n"
                    f"counter = Path({str(counter_path)!r})\n"
                    "count = int(counter.read_text() or '0') if counter.exists() else 0\n"
                    "counter.write_text(str(count + 1))\n"
                    "address = '93.184.216.34' if count == 0 else '127.0.0.1'\n"
                    "port = int(sys.argv[2])\n"
                    "print(json.dumps([[socket.AF_INET, socket.SOCK_STREAM, "
                    "socket.IPPROTO_TCP, '', [address, port]]]))\n"
                )
                target = f"http://public.example:{server.server_address[1]}/"
                with (
                    patch.object(site_audit_module, "DNS_RESOLVER_SCRIPT", rebinding_script),
                    patch.object(site_audit_module, "build_opener", side_effect=direct_opener),
                ):
                    result, _ = fetch_url(
                        target,
                        timeout=1,
                        max_bytes=1_000,
                        user_agent="test-agent",
                        allow_private=False,
                    )
                self.assertIsNone(result["status"])
                self.assertEqual(0, server.request_count)
                self.assertEqual("1", counter_path.read_text())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_pinned_http_connection_keeps_original_host_header(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.host_headers = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            with tempfile.TemporaryDirectory() as temporary_directory:
                counter_path = Path(temporary_directory) / "resolver-count.txt"
                target = f"http://original.example:{server.server_address[1]}/"
                with patch.object(
                    site_audit_module,
                    "DNS_RESOLVER_SCRIPT",
                    ipv4_resolver_script("127.0.0.1", counter_path),
                ):
                    result, _ = fetch_url(
                        target,
                        timeout=1,
                        max_bytes=1_000,
                        user_agent="test-agent",
                        allow_private=True,
                    )
                self.assertEqual(200, result["status"])
                self.assertEqual(
                    [f"original.example:{server.server_address[1]}"],
                    server.host_headers,
                )
                self.assertEqual("1", counter_path.read_text())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_pinned_https_connection_uses_original_hostname_for_tls_and_host(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            certificate_path = Path(temporary_directory) / "certificate.pem"
            key_path = Path(temporary_directory) / "key.pem"
            certificate_path.write_text(TEST_CERT_PEM, encoding="ascii")
            key_path.write_text(
                "-----BEGIN " + "PRIVATE KEY-----\n"
                + TEST_KEY_BODY
                + "-----END "
                + "PRIVATE KEY-----\n",
                encoding="ascii",
            )

            server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
            server.host_headers = []
            sni_names = []
            server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            server_context.load_cert_chain(certificate_path, key_path)
            server_context.set_servername_callback(
                lambda _socket, server_name, _context: sni_names.append(server_name)
            )
            server.socket = server_context.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            client_context = ssl.create_default_context(cafile=certificate_path)
            try:
                with tempfile.TemporaryDirectory() as resolver_directory:
                    counter_path = Path(resolver_directory) / "resolver-count.txt"
                    target = f"https://original.example:{server.server_address[1]}/"
                    with (
                        patch.object(
                            site_audit_module,
                            "DNS_RESOLVER_SCRIPT",
                            ipv4_resolver_script("127.0.0.1", counter_path),
                        ),
                        patch.object(
                            site_audit_module.ssl,
                            "create_default_context",
                            return_value=client_context,
                        ),
                    ):
                        result, _ = fetch_url(
                            target,
                            timeout=2,
                            max_bytes=1_000,
                            user_agent="test-agent",
                            allow_private=True,
                        )
                    self.assertEqual(200, result["status"])
                    self.assertEqual(["original.example"], sni_names)
                    self.assertEqual(
                        [f"original.example:{server.server_address[1]}"],
                        server.host_headers,
                    )
                    self.assertEqual("1", counter_path.read_text())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_dns_resolution_respects_the_hard_total_timeout(self) -> None:
        def slow_getaddrinfo(host, port, *args, **kwargs):
            time.sleep(0.25)
            return [
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("93.184.216.34", port),
                )
            ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            marker_path = Path(temporary_directory) / "resolver-survived.txt"
            slow_resolver_script = (
                "import time\n"
                "from pathlib import Path\n"
                "time.sleep(0.25)\n"
                f"Path({str(marker_path)!r}).write_text('alive')\n"
            )
            started = time.monotonic()
            with (
                patch.object(
                    site_audit_module.socket,
                    "getaddrinfo",
                    side_effect=slow_getaddrinfo,
                ),
                patch.object(
                    site_audit_module,
                    "DNS_RESOLVER_SCRIPT",
                    slow_resolver_script,
                    create=True,
                ),
            ):
                with self.assertRaisesRegex(AuditTimeoutError, "time limit"):
                    audit_site(
                        "http://slow-dns.example/",
                        max_pages=1,
                        timeout=1,
                        total_timeout=0.03,
                        delay=0,
                        allow_private=False,
                    )
            self.assertLess(time.monotonic() - started, 0.5)
            time.sleep(0.3)
            self.assertFalse(marker_path.exists())

    def test_dns_resolution_uses_request_timeout_without_total_timeout(self) -> None:
        def slow_getaddrinfo(host, port, *args, **kwargs):
            time.sleep(0.25)
            return [
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("93.184.216.34", port),
                )
            ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            marker_path = Path(temporary_directory) / "resolver-survived.txt"
            slow_resolver_script = (
                "import sys\n"
                "if not sys.flags.isolated:\n"
                "    raise SystemExit(9)\n"
                "import time\n"
                "from pathlib import Path\n"
                "time.sleep(0.25)\n"
                f"Path({str(marker_path)!r}).write_text('alive')\n"
            )
            started = time.monotonic()
            with (
                patch.object(
                    site_audit_module.socket,
                    "getaddrinfo",
                    side_effect=slow_getaddrinfo,
                ),
                patch.object(
                    site_audit_module,
                    "DNS_RESOLVER_SCRIPT",
                    slow_resolver_script,
                ),
            ):
                result, _ = fetch_url(
                    "http://slow-dns.example/",
                    timeout=0.01,
                    max_bytes=1_000,
                    user_agent="test-agent",
                    allow_private=False,
                )
            self.assertIsNone(result["status"])
            self.assertEqual("Target resolution timed out", result["error"])
            self.assertLess(time.monotonic() - started, 0.5)
            time.sleep(0.3)
            self.assertFalse(marker_path.exists())

    def test_initial_resolution_failures_do_not_commit_unverified_url(self) -> None:
        path_marker = "private-initial-path-marker"
        target = f"https://unresolved.example/{path_marker}?source=private"
        failures = (
            (
                TimeoutError(f"timed out while resolving {target}"),
                "Target resolution timed out",
            ),
            (
                URLError(f"failed while resolving {target}"),
                "Target resolution failed",
            ),
            (
                OSError(f"network failure while resolving {target}"),
                "Target resolution failed",
            ),
        )

        for failure, expected_error in failures:
            with self.subTest(failure=type(failure).__name__):
                with patch.object(
                    site_audit_module,
                    "resolve_url",
                    side_effect=failure,
                ):
                    result, text = fetch_url(
                        target,
                        timeout=1,
                        max_bytes=1_000,
                        user_agent="test-agent",
                        allow_private=False,
                    )

                serialized = json.dumps(result, sort_keys=True)
                self.assertIsNone(result["status"])
                self.assertIsNone(result["final_url"])
                self.assertEqual([], result["redirects"])
                self.assertEqual("", text)
                self.assertEqual(expected_error, result["error"])
                self.assertNotIn(target, serialized)
                self.assertNotIn("unresolved.example", serialized)
                self.assertNotIn(path_marker, serialized)

    def test_redirect_resolution_failures_redact_unverified_candidate(self) -> None:
        class RedirectingOpener:
            def __init__(self, location: str) -> None:
                self.location = location

            def open(self, request, timeout):
                headers = Message()
                headers["Location"] = self.location
                raise HTTPError(request.full_url, 302, "Found", headers, BytesIO())

        target = "https://verified.example/start"
        path_marker = "private-redirect-path-marker"
        candidate = (
            f"https://unverified-redirect.example/{path_marker}?source=private"
        )
        verified_addresses = (
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", 443),
            ),
        )
        failures = (
            (
                TimeoutError(f"timed out while resolving {candidate}"),
                "Redirect target resolution timed out",
            ),
            (
                URLError(f"failed while resolving {candidate}"),
                "Redirect target validation failed",
            ),
            (
                OSError(f"network failure while resolving {candidate}"),
                "Redirect target validation failed",
            ),
        )

        for failure, expected_error in failures:
            with self.subTest(failure=type(failure).__name__):
                def resolve_redirect(url, allow_private, check_control=None, timeout=10):
                    if url == target:
                        return verified_addresses
                    self.assertEqual(candidate, url)
                    raise failure

                with (
                    patch.object(
                        site_audit_module,
                        "resolve_url",
                        side_effect=resolve_redirect,
                    ),
                    patch.object(
                        site_audit_module,
                        "build_opener",
                        return_value=RedirectingOpener(candidate),
                    ),
                ):
                    result, text = fetch_url(
                        target,
                        timeout=1,
                        max_bytes=1_000,
                        user_agent="test-agent",
                        allow_private=False,
                    )

                serialized = json.dumps(result, sort_keys=True)
                self.assertIsNone(result["status"])
                self.assertEqual(target, result["final_url"])
                self.assertEqual([], result["redirects"])
                self.assertEqual("", text)
                self.assertEqual(expected_error, result["error"])
                self.assertNotIn(candidate, serialized)
                self.assertNotIn("unverified-redirect.example", serialized)
                self.assertNotIn(path_marker, serialized)

    def test_malformed_redirect_location_is_redacted_before_state_update(self) -> None:
        class RedirectingOpener:
            def __init__(self, location: str) -> None:
                self.location = location

            def open(self, request, timeout):
                headers = Message()
                headers["Location"] = self.location
                raise HTTPError(request.full_url, 302, "Found", headers, BytesIO())

        target = "https://verified.example/start"
        host_marker = "nfkc-host-marker.example"
        path_marker = "private-nfkc-path-marker"
        malformed_location = f"https://{host_marker}\uff0f{path_marker}"
        verified_addresses = (
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", 443),
            ),
        )

        with (
            patch.object(
                site_audit_module,
                "resolve_url",
                return_value=verified_addresses,
            ) as resolver,
            patch.object(
                site_audit_module,
                "build_opener",
                return_value=RedirectingOpener(malformed_location),
            ),
        ):
            result, text = fetch_url(
                target,
                timeout=1,
                max_bytes=1_000,
                user_agent="test-agent",
                allow_private=False,
            )

        serialized = json.dumps(result, sort_keys=True)
        self.assertIsNone(result["status"])
        self.assertEqual(target, result["final_url"])
        self.assertEqual([], result["redirects"])
        self.assertEqual("", text)
        self.assertEqual("Redirect target validation failed", result["error"])
        self.assertNotIn(malformed_location, serialized)
        self.assertNotIn(host_marker, serialized)
        self.assertNotIn(path_marker, serialized)
        resolver.assert_called_once_with(target, False, None, 1.0)

    def test_invalid_request_timeouts_are_rejected_before_network_setup(self) -> None:
        invalid_timeouts = (
            0,
            -1,
            float("nan"),
            float("inf"),
            float("-inf"),
            604801,
            1e20,
        )
        for timeout in invalid_timeouts:
            with self.subTest(timeout=timeout):
                with (
                    patch.object(site_audit_module.subprocess, "Popen") as resolver,
                    patch.object(site_audit_module.socket, "socket") as socket_factory,
                ):
                    with self.assertRaisesRegex(ValueError, "Per-request timeout"):
                        audit_site(
                            "http://public.example/",
                            max_pages=1,
                            timeout=timeout,
                            delay=0,
                            allow_private=False,
                        )
                resolver.assert_not_called()
                socket_factory.assert_not_called()

    def test_connect_resolved_closes_socket_when_timeout_setup_fails(self) -> None:
        class FailingSocket:
            def __init__(self) -> None:
                self.socket_closed = False

            def settimeout(self, timeout) -> None:
                raise OverflowError("timeout overflow")

            def close(self) -> None:
                self.socket_closed = True

        failing_socket = FailingSocket()
        addresses = (
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", 80),
            ),
        )
        with patch.object(site_audit_module.socket, "socket", return_value=failing_socket):
            with self.assertRaises(OverflowError):
                connect_resolved(addresses, 1, None)
        self.assertTrue(failing_socket.socket_closed)

    def test_connect_resolved_rejects_invalid_timeout_before_socket_creation(self) -> None:
        addresses = (
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", 80),
            ),
        )
        with patch.object(site_audit_module.socket, "socket") as socket_factory:
            with self.assertRaisesRegex(ValueError, "Per-request timeout"):
                connect_resolved(addresses, 604801, None)
        socket_factory.assert_not_called()

    def test_request_timeout_upper_bound_is_fixed_and_socket_representable(self) -> None:
        self.assertEqual(604800, site_audit_module.MAX_REQUEST_TIMEOUT)
        sock = socket.socket()
        try:
            sock.settimeout(site_audit_module.MAX_REQUEST_TIMEOUT)
            self.assertEqual(604800, sock.gettimeout())
        finally:
            sock.close()

    def test_https_connection_closes_socket_when_tls_setup_fails(self) -> None:
        class RawSocket:
            def __init__(self) -> None:
                self.socket_closed = False

            def close(self) -> None:
                self.socket_closed = True

        raw_socket = RawSocket()
        connection = PinnedHTTPSConnection(
            "original.example",
            resolved_addresses=(),
        )

        def fail_tls_setup(instance) -> None:
            instance.sock = raw_socket
            raise ssl.SSLError("TLS setup failed")

        with patch.object(site_audit_module.HTTPSConnection, "connect", fail_tls_setup):
            with self.assertRaises(ssl.SSLError):
                connection.connect()
        self.assertTrue(raw_socket.socket_closed)
        self.assertIsNone(connection.sock)

    def test_total_timeout_caps_page_delay(self) -> None:
        started = time.monotonic()
        with self.assertRaisesRegex(AuditTimeoutError, "time limit"):
            self.run_fixture_audit(
                max_pages=1,
                total_timeout=0.15,
                delay=0.5,
            )
        self.assertLess(time.monotonic() - started, 0.3)

    def test_cancellation_is_checked_during_page_delay(self) -> None:
        cancel_at = time.monotonic() + 0.08
        started = time.monotonic()
        with self.assertRaisesRegex(AuditCancelledError, "cancelled"):
            self.run_fixture_audit(
                max_pages=1,
                delay=0.5,
                should_cancel=lambda: time.monotonic() >= cancel_at,
            )
        self.assertLess(time.monotonic() - started, 0.25)

    def test_trickle_response_cannot_exceed_the_hard_total_timeout(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        deadline = time.monotonic() + 0.08

        def check_control() -> float:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AuditTimeoutError("Audit exceeded total time limit")
            return remaining

        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/trickle"
            with self.assertRaisesRegex(AuditTimeoutError, "time limit"):
                fetch_url(
                    target,
                    timeout=0.5,
                    max_bytes=1_000,
                    user_agent="test-agent",
                    allow_private=True,
                    check_control=check_control,
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_cancellation_is_checked_while_reading_a_response_body(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        cancel_at = time.monotonic() + 0.08

        def check_control() -> None:
            if time.monotonic() >= cancel_at:
                raise AuditCancelledError("Audit cancelled")
            return None

        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/trickle"
            with self.assertRaisesRegex(AuditCancelledError, "cancelled"):
                fetch_url(
                    target,
                    timeout=0.5,
                    max_bytes=1_000,
                    user_agent="test-agent",
                    allow_private=True,
                    check_control=check_control,
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_stalled_body_cancellation_closes_socket_and_joins_watchdog(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.stall_started = threading.Event()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        captured_sockets = []
        original_response_socket = site_audit_module.response_socket

        def capture_socket(response):
            sock = original_response_socket(response)
            if sock is not None:
                captured_sockets.append(sock)
            return sock

        def check_control() -> None:
            if (
                server.stall_started.is_set()
                and time.monotonic() - server.stall_started_at >= 0.05
            ):
                raise AuditCancelledError("Audit cancelled")
            return None

        watchers_before = sum(
            item.name == "seo-audit-body-watchdog" for item in threading.enumerate()
        )
        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/stall"
            with (
                patch.object(
                    site_audit_module,
                    "response_socket",
                    side_effect=capture_socket,
                ),
                self.assertRaisesRegex(AuditCancelledError, "cancelled"),
            ):
                fetch_url(
                    target,
                    timeout=1,
                    max_bytes=1_000,
                    user_agent="test-agent",
                    allow_private=True,
                    check_control=check_control,
                )
            self.assertLess(time.monotonic() - server.stall_started_at, 0.5)
            self.assertTrue(captured_sockets)
            self.assertTrue(all(sock.fileno() == -1 for sock in captured_sockets))
            self.assertEqual(
                watchers_before,
                sum(
                    item.name == "seo-audit-body-watchdog"
                    for item in threading.enumerate()
                ),
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_https_stalled_body_cancellation_closes_socket_and_watchdog(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            certificate_path = Path(temporary_directory) / "certificate.pem"
            key_path = Path(temporary_directory) / "key.pem"
            certificate_path.write_text(TEST_CERT_PEM, encoding="ascii")
            key_path.write_text(
                "-----BEGIN " + "PRIVATE KEY-----\n"
                + TEST_KEY_BODY
                + "-----END "
                + "PRIVATE KEY-----\n",
                encoding="ascii",
            )

            server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
            server.stall_started = threading.Event()
            server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            server_context.load_cert_chain(certificate_path, key_path)
            server.socket = server_context.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            client_context = ssl.create_default_context(cafile=certificate_path)
            captured_sockets = []
            original_response_socket = site_audit_module.response_socket

            def capture_socket(response):
                sock = original_response_socket(response)
                if sock is not None:
                    captured_sockets.append(sock)
                return sock

            def check_control() -> None:
                if (
                    server.stall_started.is_set()
                    and time.monotonic() - server.stall_started_at >= 0.05
                ):
                    raise AuditCancelledError("Audit cancelled")
                return None

            watchers_before = sum(
                item.name == "seo-audit-body-watchdog"
                for item in threading.enumerate()
            )
            try:
                target = f"https://original.example:{server.server_address[1]}/stall"
                with (
                    patch.object(
                        site_audit_module,
                        "DNS_RESOLVER_SCRIPT",
                        ipv4_resolver_script("127.0.0.1"),
                    ),
                    patch.object(
                        site_audit_module.ssl,
                        "create_default_context",
                        return_value=client_context,
                    ),
                    patch.object(
                        site_audit_module,
                        "response_socket",
                        side_effect=capture_socket,
                    ),
                    self.assertRaisesRegex(AuditCancelledError, "cancelled"),
                ):
                    fetch_url(
                        target,
                        timeout=1,
                        max_bytes=1_000,
                        user_agent="test-agent",
                        allow_private=True,
                        check_control=check_control,
                    )
                self.assertLess(time.monotonic() - server.stall_started_at, 0.5)
                self.assertTrue(captured_sockets)
                self.assertTrue(all(sock.fileno() == -1 for sock in captured_sockets))
                self.assertEqual(
                    watchers_before,
                    sum(
                        item.name == "seo-audit-body-watchdog"
                        for item in threading.enumerate()
                    ),
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_stalled_http_error_body_honors_total_timeout_and_joins_watchdog(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.stall_started = threading.Event()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        deadline = None

        def check_control() -> float | None:
            nonlocal deadline
            if server.stall_started.is_set() and deadline is None:
                deadline = server.stall_started_at + 0.05
            if deadline is None:
                return None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AuditTimeoutError("Audit exceeded total time limit")
            return remaining

        watchers_before = sum(
            item.name == "seo-audit-body-watchdog" for item in threading.enumerate()
        )
        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/error-stall"
            with self.assertRaisesRegex(AuditTimeoutError, "time limit"):
                fetch_url(
                    target,
                    timeout=1,
                    max_bytes=1_000,
                    user_agent="test-agent",
                    allow_private=True,
                    check_control=check_control,
                )
            self.assertLess(time.monotonic() - server.stall_started_at, 0.5)
            self.assertEqual(
                watchers_before,
                sum(
                    item.name == "seo-audit-body-watchdog"
                    for item in threading.enumerate()
                ),
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_reader_base_exceptions_are_not_replaced_by_watchdog_error(self) -> None:
        for original_error in (
            KeyboardInterrupt("keyboard-interrupt-marker"),
            SystemExit("system-exit-marker"),
        ):
            with self.subTest(error=type(original_error).__name__):
                response_socket, peer_socket = socket.socketpair()
                watchdog_triggered = threading.Event()

                class InterruptingResponse:
                    def __init__(self, sock) -> None:
                        self._sock = sock

                    def read1(self, _size=-1):
                        if not watchdog_triggered.wait(1):
                            raise RuntimeError("watchdog did not run")
                        deadline = time.monotonic() + 1
                        while self._sock.fileno() != -1 and time.monotonic() < deadline:
                            time.sleep(0.001)
                        raise original_error

                def check_control() -> None:
                    if threading.current_thread().name == "seo-audit-body-watchdog":
                        watchdog_triggered.set()
                        raise AuditTimeoutError("watchdog-timeout-marker")
                    return None

                try:
                    with self.assertRaises(type(original_error)) as raised:
                        site_audit_module.read_response_body(
                            InterruptingResponse(response_socket),
                            timeout=1,
                            max_bytes=1_000,
                            check_control=check_control,
                        )
                    self.assertIs(original_error, raised.exception)
                finally:
                    response_socket.close()
                    peer_socket.close()

    def test_blocking_control_callback_cannot_block_watchdog_cleanup(self) -> None:
        response_socket, peer_socket = socket.socketpair()
        callback_started = threading.Event()
        release_callback = threading.Event()
        original_error = RuntimeError("reader-failure-marker")
        outcome = {}

        class FailingResponse:
            def __init__(self, sock) -> None:
                self._sock = sock

            def read1(self, _size=-1):
                if not callback_started.wait(1):
                    raise RuntimeError("watchdog callback did not start")
                raise original_error

        def check_control() -> None:
            if threading.current_thread().name == "seo-audit-body-watchdog":
                callback_started.set()
                release_callback.wait(2)
            return None

        def run_read() -> None:
            try:
                site_audit_module.read_response_body(
                    FailingResponse(response_socket),
                    timeout=1,
                    max_bytes=1_000,
                    check_control=check_control,
                )
            except BaseException as exc:
                outcome["error"] = exc

        watchers_before = sum(
            item.name == "seo-audit-body-watchdog" for item in threading.enumerate()
        )
        worker = threading.Thread(target=run_read, daemon=True)
        started = time.monotonic()
        worker.start()
        worker.join(timeout=0.45)
        finished_within_bound = not worker.is_alive()
        elapsed = time.monotonic() - started
        release_callback.set()
        worker.join(timeout=2)
        deadline = time.monotonic() + 2
        while (
            sum(
                item.name == "seo-audit-body-watchdog"
                for item in threading.enumerate()
            )
            != watchers_before
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        try:
            self.assertTrue(finished_within_bound)
            self.assertLess(elapsed, 0.5)
            self.assertIs(original_error, outcome.get("error"))
            self.assertEqual(
                watchers_before,
                sum(
                    item.name == "seo-audit-body-watchdog"
                    for item in threading.enumerate()
                ),
            )
        finally:
            release_callback.set()
            worker.join(timeout=2)
            response_socket.close()
            peer_socket.close()

    def test_normal_watchdog_callback_is_stopped_and_joined(self) -> None:
        response_socket, peer_socket = socket.socketpair()

        class EmptyResponse:
            def __init__(self, sock) -> None:
                self._sock = sock

            def read1(self, _size=-1):
                return b""

        watchers_before = sum(
            item.name == "seo-audit-body-watchdog" for item in threading.enumerate()
        )
        try:
            body = site_audit_module.read_response_body(
                EmptyResponse(response_socket),
                timeout=1,
                max_bytes=1_000,
                check_control=lambda: None,
            )
            self.assertEqual(b"", body)
            self.assertEqual(
                watchers_before,
                sum(
                    item.name == "seo-audit-body-watchdog"
                    for item in threading.enumerate()
                ),
            )
        finally:
            response_socket.close()
            peer_socket.close()

    def test_http_error_body_timeout_maps_to_managed_timeout(self) -> None:
        body_reads = 0

        class TimeoutBody(BytesIO):
            def read(self, _size=-1):
                nonlocal body_reads
                body_reads += 1
                raise TimeoutError("raw socket timeout")

            def read1(self, _size=-1):
                nonlocal body_reads
                body_reads += 1
                raise TimeoutError("raw socket timeout")

        class ErrorOpener:
            def open(self, request, timeout):
                headers = Message()
                headers["Content-Type"] = "text/plain"
                raise HTTPError(
                    request.full_url,
                    500,
                    "Server Error",
                    headers,
                    TimeoutBody(),
                )

        def check_control() -> float:
            if body_reads:
                raise AuditTimeoutError("Audit exceeded total time limit")
            return 1

        with patch.object(site_audit_module, "build_opener", return_value=ErrorOpener()):
            with self.assertRaisesRegex(AuditTimeoutError, "time limit"):
                fetch_url(
                    "https://127.0.0.1/",
                    timeout=1,
                    max_bytes=1_000,
                    user_agent="test-agent",
                    allow_private=True,
                    check_control=check_control,
                )
        self.assertEqual(1, body_reads)

    def test_cancellation_before_first_request_raises_specific_error(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.request_count = 0
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/"
            with self.assertRaisesRegex(AuditCancelledError, "cancelled"):
                audit_site(target, allow_private=True, should_cancel=lambda: True)
            self.assertEqual(0, server.request_count)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_cancellation_during_page_traversal_does_not_return_partial_success(self) -> None:
        cancelled = False
        progress_events = []

        def on_progress(progress) -> None:
            nonlocal cancelled
            progress_events.append(progress)
            cancelled = progress["pages_processed"] >= 1

        with self.assertRaisesRegex(AuditCancelledError, "cancelled"):
            self.run_fixture_audit(
                should_cancel=lambda: cancelled,
                on_progress=on_progress,
            )
        self.assertEqual(1, len(progress_events))
        self.assertEqual(1, progress_events[0]["pages_processed"])

    def test_cancellation_after_final_page_does_not_return_success(self) -> None:
        cancelled = False

        def on_progress(_progress) -> None:
            nonlocal cancelled
            cancelled = True

        with self.assertRaisesRegex(AuditCancelledError, "cancelled"):
            self.run_fixture_audit(
                max_pages=1,
                should_cancel=lambda: cancelled,
                on_progress=on_progress,
            )

    def test_progress_is_emitted_after_every_processed_page(self) -> None:
        progress_events = []
        try:
            result, _ = self.run_fixture_audit(on_progress=progress_events.append)
        except TypeError as exc:
            self.fail(f"audit_site must accept on_progress: {exc}")
        self.assertEqual(result["summary"]["pages_crawled"], len(progress_events))
        self.assertEqual([1, 2], [item["pages_processed"] for item in progress_events])
        self.assertTrue(all(item["phase"] == "crawl" for item in progress_events))

    def test_total_timeout_is_independent_from_per_request_timeout(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.response_delay = 0.1
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/"
            with self.assertRaisesRegex(AuditTimeoutError, "time limit"):
                audit_site(
                    target,
                    max_pages=1,
                    timeout=2,
                    total_timeout=0.02,
                    delay=0,
                    allow_private=True,
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_total_timeout_during_report_assembly_does_not_return_success(self) -> None:
        expired = False
        original_build_agent_prompts = site_audit_module.build_agent_prompts

        def fake_monotonic() -> float:
            return 10.0 if expired else 0.0

        def expire_during_report(audit):
            nonlocal expired
            expired = True
            return original_build_agent_prompts(audit)

        with (
            patch.object(site_audit_module.time, "monotonic", side_effect=fake_monotonic),
            patch.object(site_audit_module, "build_agent_prompts", side_effect=expire_during_report),
        ):
            with self.assertRaisesRegex(AuditTimeoutError, "time limit"):
                self.run_fixture_audit(total_timeout=1)

    def test_rejects_non_public_credentials_and_non_http_targets(self) -> None:
        blocked_urls = (
            "http://127.0.0.1",
            "http://[::1]",
            "http://169.254.169.254",
            "http://10.0.0.1",
            "http://100.100.100.200",
            "http://100.64.0.1",
        )
        for target in blocked_urls:
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, "Private or non-public address blocked"):
                    validate_url(target, allow_private=False)

        with self.assertRaisesRegex(ValueError, "credentials"):
            validate_url("http://user:pass@example.com", allow_private=False)
        for target in ("ftp://example.com", "file:///etc/passwd"):
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, "Only absolute http/https URLs"):
                    validate_url(target, allow_private=False)

    def test_invalid_urls_never_echo_credentials_or_original_input(self) -> None:
        targets = (
            "ftp://user:supersecret@example.com/path",
            "http://user:supersecret@",
            "ftp://example.com/private-path-token",
        )
        for target in targets:
            with self.subTest(target=target):
                with self.assertRaises(ValueError) as raised:
                    validate_url(target, allow_private=False)
                message = str(raised.exception)
                self.assertNotIn(target, message)
                self.assertNotIn("user", message)
                self.assertNotIn("supersecret", message)
                self.assertNotIn("private-path-token", message)

    def test_cli_redacts_invalid_credential_urls(self) -> None:
        targets = (
            "ftp://user:supersecret@example.com/path",
            "http://user:supersecret@",
        )
        for target in targets:
            with self.subTest(target=target):
                stderr = StringIO()
                with (
                    patch.object(sys, "argv", ["site_audit.py", target]),
                    patch.object(sys, "stderr", stderr),
                ):
                    exit_code = site_audit_module.main()
                output = stderr.getvalue()
                self.assertEqual(2, exit_code)
                self.assertNotIn(target, output)
                self.assertNotIn("user", output)
                self.assertNotIn("supersecret", output)

    def test_cli_rejects_invalid_timeouts_without_exposing_target(self) -> None:
        target = "https://example.com/private-target-token"
        for timeout in ("inf", "-1"):
            with self.subTest(timeout=timeout):
                stderr = StringIO()
                stdout = StringIO()
                with (
                    patch.object(
                        sys,
                        "argv",
                        ["site_audit.py", target, "--timeout", timeout],
                    ),
                    patch.object(sys, "stderr", stderr),
                    patch.object(sys, "stdout", stdout),
                    patch.object(site_audit_module.subprocess, "Popen") as resolver,
                ):
                    exit_code = site_audit_module.main()
                output = stderr.getvalue() + stdout.getvalue()
                self.assertEqual(2, exit_code)
                self.assertIn("Per-request timeout", output)
                self.assertNotIn(target, output)
                self.assertNotIn("private-target-token", output)
                resolver.assert_not_called()

    def test_invalid_max_redirects_are_rejected_before_network_setup(self) -> None:
        target = "https://example.com/private-target-token"
        for max_redirects in (-1, True, 1.5, "1", object()):
            with self.subTest(max_redirects=max_redirects):
                with (
                    patch.object(site_audit_module.subprocess, "Popen") as resolver,
                    patch.object(site_audit_module.socket, "socket") as socket_factory,
                ):
                    with self.assertRaises(ValueError) as raised:
                        fetch_url(
                            target,
                            timeout=1,
                            max_bytes=1_000,
                            user_agent="test-agent",
                            allow_private=False,
                            max_redirects=max_redirects,
                        )
                message = str(raised.exception)
                self.assertIn("max_redirects", message)
                self.assertNotIn(target, message)
                self.assertNotIn("private-target-token", message)
                resolver.assert_not_called()
                socket_factory.assert_not_called()

    def test_negative_max_redirects_cannot_bypass_credential_validation(self) -> None:
        target = "http://user:supersecret@example.com/private-target-token"
        with patch.object(site_audit_module.subprocess, "Popen") as resolver:
            with self.assertRaises(ValueError) as raised:
                fetch_url(
                    target,
                    timeout=1,
                    max_bytes=1_000,
                    user_agent="test-agent",
                    allow_private=False,
                    max_redirects=-1,
                )
        message = str(raised.exception)
        self.assertIn("credentials", message)
        self.assertNotIn(target, message)
        self.assertNotIn("supersecret", message)
        resolver.assert_not_called()

    def test_cli_rejects_invalid_max_redirects_without_exposing_target(self) -> None:
        target = "https://example.com/private-target-token"
        for max_redirects in ("-1", "1.5"):
            with self.subTest(max_redirects=max_redirects):
                stderr = StringIO()
                stdout = StringIO()
                with (
                    patch.object(
                        sys,
                        "argv",
                        [
                            "site_audit.py",
                            target,
                            "--max-redirects",
                            max_redirects,
                        ],
                    ),
                    patch.object(sys, "stderr", stderr),
                    patch.object(sys, "stdout", stdout),
                    patch.object(site_audit_module.subprocess, "Popen") as resolver,
                    self.assertRaises(SystemExit) as raised,
                ):
                    site_audit_module.main()
                output = stderr.getvalue() + stdout.getvalue()
                self.assertEqual(2, raised.exception.code)
                self.assertIn("max_redirects", output)
                self.assertNotIn(target, output)
                self.assertNotIn("private-target-token", output)
                resolver.assert_not_called()

    def test_last_redirect_is_validated_before_limit_or_history_update(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.request_count = 0
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        original_resolve_url = site_audit_module.resolve_url
        local_addresses = socket.getaddrinfo(
            "127.0.0.1",
            server.server_address[1],
            type=socket.SOCK_STREAM,
            flags=socket.AI_NUMERICHOST,
        )

        def resolve_redirect_test_url(url, allow_private, check_control=None, timeout=10):
            if site_audit_module.urlsplit(url).hostname == "public.example":
                return tuple(local_addresses)
            return original_resolve_url(url, allow_private, check_control, timeout)

        malicious_locations = (
            "file:///private-target-token",
            "http://user:supersecret@example.com/private-target-token",
            "http://127.0.0.1/private-target-token",
            "http://169.254.169.254/latest/meta-data/private-target-token",
        )
        try:
            target = (
                f"http://public.example:{server.server_address[1]}/redirect-start"
            )
            for location in malicious_locations:
                with self.subTest(location=location):
                    server.redirect_location = location
                    server.request_count = 0
                    with (
                        patch.object(
                            site_audit_module,
                            "resolve_url",
                            side_effect=resolve_redirect_test_url,
                        ),
                    ):
                        result, text = fetch_url(
                            target,
                            timeout=2,
                            max_bytes=1_000,
                            user_agent="test-agent",
                            allow_private=False,
                            max_redirects=1,
                        )
                    middle = (
                        f"http://public.example:{server.server_address[1]}"
                        "/redirect-middle"
                    )
                    serialized = json.dumps(result, sort_keys=True)
                    self.assertIsNone(result["status"])
                    self.assertEqual("Redirect target validation failed", result["error"])
                    self.assertEqual(middle, result["final_url"])
                    self.assertEqual(
                        [{"status": 302, "from": target, "to": middle}],
                        result["redirects"],
                    )
                    self.assertEqual("", text)
                    self.assertNotIn(location, serialized)
                    self.assertNotIn("private-target-token", serialized)
                    self.assertNotIn("supersecret", serialized)
                    self.assertEqual(2, server.request_count)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_max_redirects_zero_validates_location_without_exposing_it(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.redirect_location = "/about"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/redirect-start"
            result, _ = fetch_url(
                target,
                timeout=2,
                max_bytes=1_000,
                user_agent="test-agent",
                allow_private=True,
                max_redirects=0,
            )
            self.assertIsNone(result["status"])
            self.assertIn("Too many redirects", result["error"])
            self.assertEqual([], result["redirects"])
            self.assertEqual(target, result["final_url"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_rejects_public_redirects_to_private_and_metadata_addresses(self) -> None:
        class RedirectingOpener:
            def __init__(self, location: str) -> None:
                self.location = location

            def open(self, request, timeout):
                headers = Message()
                headers["Location"] = self.location
                raise HTTPError(request.full_url, 302, "Found", headers, BytesIO())

        for location in (
            "http://127.0.0.1/private",
            "http://169.254.169.254/latest/meta-data",
            "http://100.100.100.200/latest/meta-data",
            "http://100.64.0.1/shared-space",
        ):
            with self.subTest(location=location):
                with (
                    patch.object(
                        site_audit_module,
                        "DNS_RESOLVER_SCRIPT",
                        ipv4_resolver_script("93.184.216.34"),
                    ),
                    patch.object(site_audit_module, "build_opener", return_value=RedirectingOpener(location)),
                ):
                    result, text = fetch_url(
                        "https://public.example/",
                        timeout=1,
                        max_bytes=1_000,
                        user_agent="test-agent",
                        allow_private=False,
                    )
                serialized = json.dumps(result, sort_keys=True)
                self.assertIsNone(result["status"])
                self.assertEqual("Redirect target validation failed", result["error"])
                self.assertEqual("https://public.example/", result["final_url"])
                self.assertEqual([], result["redirects"])
                self.assertEqual("", text)
                self.assertNotIn(location, serialized)

    def test_missing_robots_is_informational(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        server.robots_missing = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            target = f"http://127.0.0.1:{server.server_address[1]}/"
            result = audit_site(
                target,
                max_pages=1,
                timeout=2,
                delay=0,
                max_sitemaps=1,
                allow_private=True,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        finding = next(item for item in result["findings"] if item["code"] == "robots_unavailable")
        self.assertEqual("info", finding["severity"])
        self.assertIn("没有显式抓取策略", finding["issue"])


if __name__ == "__main__":
    unittest.main()
