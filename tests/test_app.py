from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sys
import threading
import unittest
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import app as app_module  # noqa: E402


AuditAppHandler = app_module.AuditAppHandler
AuditRequestError = getattr(app_module, "AuditRequestError", ValueError)
WEB_DIR = app_module.WEB_DIR


def parse_audit_request(payload: object) -> tuple[str, int]:
    parser = getattr(app_module, "parse_audit_request", None)
    if parser is None:
        raise AssertionError("parse_audit_request is not implemented")
    return parser(payload)


def parse_browser_render_option(payload: dict[str, object]) -> bool:
    parser = getattr(app_module, "parse_browser_render_option", None)
    if parser is None:
        raise AssertionError("parse_browser_render_option is not implemented")
    return parser(payload)


class AppRequestTests(unittest.TestCase):
    def test_adds_https_when_scheme_is_omitted(self) -> None:
        url, max_pages = parse_audit_request({"url": "example.com", "max_pages": "25"})
        self.assertEqual("https://example.com", url)
        self.assertEqual(25, max_pages)

    def test_rejects_url_with_credentials(self) -> None:
        with self.assertRaises(AuditRequestError):
            parse_audit_request({"url": "https://name:secret@example.com"})

    def test_rejects_unusually_long_target_urls(self) -> None:
        with self.assertRaises(AuditRequestError):
            parse_audit_request({"url": "https://example.com/" + "x" * 2_048})

    def test_rejects_page_limit_outside_public_boundary(self) -> None:
        for value in (0, 301, True, "not-a-number"):
            with self.subTest(value=value), self.assertRaises(AuditRequestError):
                parse_audit_request({"url": "https://example.com", "max_pages": value})

    def test_accepts_300_page_limit(self) -> None:
        _, max_pages = parse_audit_request(
            {"url": "https://example.com", "max_pages": 300}
        )
        self.assertEqual(300, max_pages)

    def test_browser_render_option_defaults_off_and_requires_json_boolean(self) -> None:
        self.assertFalse(parse_browser_render_option({"url": "https://example.com"}))
        self.assertTrue(
            parse_browser_render_option(
                {"url": "https://example.com", "render_browser": True}
            )
        )
        for value in ("true", 1, None):
            with self.subTest(value=value), self.assertRaises(AuditRequestError):
                parse_browser_render_option(
                    {"url": "https://example.com", "render_browser": value}
                )

    def test_web_entrypoint_waits_for_user_url_before_showing_report(self) -> None:
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        script = (WEB_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="audit-form"', html)
        self.assertIn('id="target-url"', html)
        self.assertIn('id="max-pages"', html)
        self.assertIn('id="external-evidence-file"', html)
        self.assertIn('id="render-browser"', html)
        self.assertIn('href="/docs/browser-rendering.md"', html)
        self.assertIn('id="external-evidence-section"', html)
        self.assertIn('href="/docs/external-evidence.md"', html)
        self.assertIn('value="300"', html)
        self.assertIn('id="report" class="report hidden"', html)
        self.assertIn("输入网址并开始巡检", html)
        self.assertIn("form.addEventListener('submit'", script)
        self.assertIn("fetch('/api/audit'", script)
        self.assertIn("renderReport(data)", script)
        self.assertIn('id="audit-progress"', html)
        self.assertIn('id="cancel-audit"', html)
        self.assertIn("/api/audit/status", script)
        self.assertIn("/api/audit/cancel", script)
        self.assertIn("render_browser: browserRenderCheckbox.checked", script)

        input_tag = re.search(r'<input[^>]+id="target-url"[^>]*>', html)
        self.assertIsNotNone(input_tag)
        self.assertNotIn(" value=", input_tag.group(0))

    def test_web_entrypoint_supports_complete_chinese_english_switching(self) -> None:
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        script = (WEB_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="language-switcher"', html)
        self.assertIn('data-language="zh-CN"', html)
        self.assertIn('data-language="en"', html)
        self.assertIn("SearchScope | Independent Site SEO/GEO Auditor", script)
        self.assertIn("Enter a URL and Start Audit", script)
        self.assertIn("Audit Results", script)
        self.assertIn("document.documentElement.lang", script)
        self.assertIn("localStorage", script)

    def test_web_entrypoint_links_supported_agents(self) -> None:
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        for website in (
            "https://openai.com/codex/",
            "https://openclaw.ai/",
            "https://hermes-agent.nousresearch.com/",
            "https://claude.com/product/claude-code",
        ):
            self.assertIn(website, html)

    def test_health_reports_public_read_only_mode(self) -> None:
        server, thread, connection = self._start_server()
        try:
            connection.request("GET", "/api/health")
            response = connection.getresponse()
            payload = json.loads(response.read())

            self.assertEqual(200, response.status)
            self.assertEqual(
                {
                    "ok": True,
                    "service": "searchscope",
                    "mode": "read_only",
                    "auditExecution": True,
                },
                payload,
            )
        finally:
            self._stop_server(server, thread, connection)

    def test_external_evidence_format_is_available_from_the_local_app(self) -> None:
        server, thread, connection = self._start_server()
        try:
            connection.request("GET", "/docs/external-evidence.md")
            response = connection.getresponse()
            content = response.read().decode("utf-8")

            self.assertEqual(200, response.status)
            self.assertIn("schema_version", content)
            self.assertIn("256 KiB", content)
        finally:
            self._stop_server(server, thread, connection)

    def test_public_audit_invokes_engine_with_private_access_disabled(self) -> None:
        audit_result = {
            "meta": {"target": "https://example.com"},
            "summary": {"html_pages": 1, "failed_pages": 0},
            "strengths": [],
            "findings": [],
            "recommendations": [],
            "agent_prompts": [],
        }
        server, thread, connection = self._start_server()
        try:
            with (
                patch(
                    "app.audit_site", return_value=audit_result, create=True
                ) as audit_site,
                patch(
                    "app.markdown_report", return_value="# report", create=True
                ) as markdown_report,
            ):
                response, payload = self._post_json(
                    connection,
                    {"url": "example.com", "max_pages": 10},
                )

            self.assertEqual(200, response.status)
            self.assertEqual(audit_result, payload["audit"])
            self.assertEqual("# report", payload["markdown"])
            kwargs = audit_site.call_args.kwargs
            self.assertEqual("https://example.com", audit_site.call_args.args[0])
            self.assertEqual(10, kwargs["max_pages"])
            self.assertEqual(10, kwargs["timeout"])
            self.assertEqual(0.1, kwargs["delay"])
            self.assertEqual(5_000_000, kwargs["max_bytes"])
            self.assertEqual(10, kwargs["max_sitemaps"])
            self.assertFalse(kwargs["allow_private"])
            self.assertFalse(kwargs["render_browser"])
            self.assertEqual(app_module.WEB_TOTAL_TIMEOUT_SECONDS, kwargs["total_timeout"])
            self.assertTrue(callable(kwargs["should_cancel"]))
            self.assertTrue(callable(kwargs["on_progress"]))
            markdown_report.assert_called_once_with(audit_result)
        finally:
            self._stop_server(server, thread, connection)

    def test_browser_render_opt_in_reaches_audit_engine(self) -> None:
        audit_result = {
            "meta": {"target": "https://example.com"},
            "summary": {"html_pages": 1, "failed_pages": 0},
            "strengths": [],
            "findings": [],
            "recommendations": [],
            "agent_prompts": [],
        }
        server, thread, connection = self._start_server()
        try:
            with (
                patch("app.audit_site", return_value=audit_result, create=True) as audit_site,
                patch("app.markdown_report", return_value="# report", create=True),
            ):
                response, _ = self._post_json(
                    connection,
                    {"url": "https://example.com", "max_pages": 10, "render_browser": True},
                )

            self.assertEqual(200, response.status)
            self.assertTrue(audit_site.call_args.kwargs["render_browser"])
        finally:
            self._stop_server(server, thread, connection)

    def test_main_binds_only_to_loopback_by_default(self) -> None:
        with (
            patch.dict(os.environ, {"PORT": "8123"}),
            patch("app.ThreadingHTTPServer") as server_type,
        ):
            server_type.return_value.serve_forever.side_effect = KeyboardInterrupt
            self.assertEqual(0, app_module.main())

        server_type.assert_called_once_with(("127.0.0.1", 8123), AuditAppHandler)
        server_type.return_value.server_close.assert_called_once()

    def test_public_audit_timeout_returns_gateway_timeout_without_target(self) -> None:
        server, thread, connection = self._start_server()
        try:
            with patch(
                "app.audit_site",
                side_effect=app_module.AuditTimeoutError("Audit exceeded total time limit"),
            ):
                response, payload = self._post_json(
                    connection,
                    {"url": "https://example.com/private-path", "max_pages": 10},
                )

            self.assertEqual(504, response.status)
            self.assertIn("时限", payload["error"])
            self.assertNotIn("private-path", json.dumps(payload))
        finally:
            self._stop_server(server, thread, connection)

    def test_cancel_endpoint_stops_active_audit_without_returning_partial_success(self) -> None:
        server, thread, _ = self._start_server()
        audit_started = threading.Event()
        audit_result: dict[str, object] = {}
        audit_connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)

        def cancelable_audit(url: str, *, should_cancel, **kwargs):  # noqa: ANN001
            audit_started.set()
            self.assertTrue(app_module.CURRENT_AUDIT.cancel_event.wait(timeout=2))
            self.assertTrue(should_cancel())
            raise app_module.AuditCancelledError("Audit cancelled")

        def send_audit() -> None:
            response, payload = self._post_json(
                audit_connection,
                {"url": "https://example.com", "max_pages": 10},
            )
            audit_result.update(status=response.status, payload=payload)

        audit_thread = threading.Thread(target=send_audit, daemon=True)
        try:
            with patch("app.audit_site", side_effect=cancelable_audit):
                audit_thread.start()
                self.assertTrue(audit_started.wait(timeout=2))
                cancel_connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
                try:
                    cancel_connection.request(
                        "POST",
                        "/api/audit/cancel",
                        body=b"{}",
                        headers={"Content-Type": "application/json", "X-SearchScope-Request": "same-origin"},
                    )
                    cancel_response = cancel_connection.getresponse()
                    cancel_payload = json.loads(cancel_response.read())
                finally:
                    cancel_connection.close()
                audit_thread.join(timeout=3)

            self.assertEqual(202, cancel_response.status)
            self.assertTrue(cancel_payload["cancel_requested"])
            self.assertEqual(409, audit_result["status"])
            self.assertIn("已取消", audit_result["payload"]["error"])
        finally:
            audit_connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_public_audit_returns_private_target_error_without_leaking_input(self) -> None:
        server, thread, connection = self._start_server()
        try:
            with patch(
                "app.audit_site",
                side_effect=ValueError("Private or non-public address blocked"),
                create=True,
            ):
                response, payload = self._post_json(
                    connection,
                    {"url": "http://127.0.0.1", "max_pages": 10},
                )

            self.assertEqual(400, response.status)
            self.assertEqual(
                "Private or non-public address blocked",
                payload["error"],
            )
            self.assertNotIn("127.0.0.1", json.dumps(payload))
        finally:
            self._stop_server(server, thread, connection)

    def test_audit_rejects_form_encoded_request_bodies(self) -> None:
        server, thread, connection = self._start_server()
        try:
            with patch("app.audit_site") as audit_site:
                connection.request(
                    "POST",
                    "/api/audit",
                    body=b'{"url":"https://example.com","max_pages":10}',
                    headers={"Content-Type": "text/plain"},
                )
                response = connection.getresponse()
                payload = json.loads(response.read())

            self.assertEqual(415, response.status)
            self.assertIn("JSON", payload["error"])
            audit_site.assert_not_called()
        finally:
            self._stop_server(server, thread, connection)

    def test_cancel_endpoint_requires_same_origin_request_header(self) -> None:
        server, thread, connection = self._start_server()
        try:
            connection.request(
                "POST",
                "/api/audit/cancel",
                body=b"{}",
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            payload = json.loads(response.read())

            self.assertEqual(403, response.status)
            self.assertIn("取消请求", payload["error"])
        finally:
            self._stop_server(server, thread, connection)

    def test_external_evidence_is_summarized_without_echoing_raw_data(self) -> None:
        audit_result = {
            "meta": {"target": "https://example.com"},
            "summary": {"html_pages": 1, "failed_pages": 0},
            "strengths": [],
            "findings": [],
            "recommendations": [],
            "agent_prompts": [],
        }
        package = {
            "schema_version": 1,
            "search_console": {
                "period_start": "2026-10-01",
                "period_end": "2026-10-14",
                "rows": [
                    {
                        "url": "https://example.com/page?private=query-value",
                        "clicks": 2,
                        "impressions": 10,
                        "position": 5.0,
                    }
                ],
            },
        }
        server, thread, connection = self._start_server()
        try:
            with (
                patch("app.audit_site", return_value=audit_result),
                patch("app.markdown_report", return_value="# report") as markdown_report,
            ):
                response, payload = self._post_json(
                    connection,
                    {"url": "https://example.com", "max_pages": 10, "external_evidence": package},
                )

            self.assertEqual(200, response.status)
            self.assertEqual(2, payload["audit"]["external_evidence"]["search_console"]["clicks"])
            self.assertFalse(payload["audit"]["external_evidence"]["affects_score"])
            self.assertNotIn("private=query-value", json.dumps(payload))
            markdown_report.assert_called_once_with(payload["audit"])
        finally:
            self._stop_server(server, thread, connection)

    def test_invalid_external_evidence_is_rejected_before_network_audit(self) -> None:
        server, thread, connection = self._start_server()
        try:
            with patch("app.audit_site") as audit_site:
                response, payload = self._post_json(
                    connection,
                    {"url": "https://example.com", "external_evidence": {"schema_version": 2}},
                )

            self.assertEqual(400, response.status)
            self.assertIn("版本", payload["error"])
            audit_site.assert_not_called()
        finally:
            self._stop_server(server, thread, connection)

    def test_oversized_external_evidence_is_rejected_before_network_audit(self) -> None:
        server, thread, connection = self._start_server()
        try:
            evidence = {
                "schema_version": 1,
                "answer_engine_samples": [
                    {"engine": "x" * 262_145, "checked_at": "2026-10-17", "samples": [{"cited_urls": []}]}
                ],
            }
            with patch("app.audit_site") as audit_site:
                response, payload = self._post_json(
                    connection,
                    {"url": "https://example.com", "external_evidence": evidence},
                )

            self.assertEqual(400, response.status)
            self.assertIn("256 KiB", payload["error"])
            audit_site.assert_not_called()
        finally:
            self._stop_server(server, thread, connection)

    def test_deeply_nested_json_returns_bad_request(self) -> None:
        server, thread, connection = self._start_server()
        try:
            connection.request(
                "POST",
                "/api/audit",
                body=(b"[" * 15_000 + b"0" + b"]" * 15_000),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            payload = json.loads(response.read())

            self.assertEqual(400, response.status)
            self.assertIn("层级", payload["error"])
        finally:
            self._stop_server(server, thread, connection)

    def test_audit_status_reports_progress_without_exposing_current_url(self) -> None:
        audit_result = {
            "meta": {"target": "https://example.com"},
            "summary": {"html_pages": 1, "failed_pages": 0},
            "strengths": [],
            "findings": [],
            "recommendations": [],
            "agent_prompts": [],
        }
        server, thread, connection = self._start_server()
        try:
            def audit_with_progress(url: str, *, on_progress, **kwargs):  # noqa: ANN001
                on_progress(
                    {
                        "phase": "crawl",
                        "pages_processed": 3,
                        "max_pages": 10,
                        "current_url": "https://example.com/private-path",
                    }
                )
                return audit_result

            with (
                patch("app.audit_site", side_effect=audit_with_progress),
                patch("app.markdown_report", return_value="# report"),
            ):
                response, _ = self._post_json(
                    connection,
                    {"url": "https://example.com", "max_pages": 10},
                )
            self.assertEqual(200, response.status)

            connection.request("GET", "/api/audit/status")
            status_response = connection.getresponse()
            status = json.loads(status_response.read())

            self.assertEqual(200, status_response.status)
            self.assertFalse(status["running"])
            self.assertEqual("completed", status["status"])
            self.assertEqual(3, status["pages_processed"])
            self.assertEqual(10, status["max_pages"])
            self.assertNotIn("current_url", status)
            self.assertNotIn("private-path", json.dumps(status))
        finally:
            self._stop_server(server, thread, connection)

    def test_readme_documents_direct_public_audit_contract(self) -> None:
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("本地只读巡检接口：`POST /api/audit`", readme)
        self.assertIn("最多巡检 300 个同源页面", readme)
        self.assertNotIn("`POST /api/audit` 固定返回 HTTP `410`", readme)

    @staticmethod
    def _start_server() -> tuple[ThreadingHTTPServer, threading.Thread, HTTPConnection]:
        server = ThreadingHTTPServer(("127.0.0.1", 0), AuditAppHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        return server, thread, connection

    @staticmethod
    def _stop_server(
        server: ThreadingHTTPServer,
        thread: threading.Thread,
        connection: HTTPConnection,
    ) -> None:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    @staticmethod
    def _post_json(
        connection: HTTPConnection,
        payload: dict[str, object],
    ) -> tuple[object, dict[str, object]]:
        body = json.dumps(payload).encode("utf-8")
        connection.request(
            "POST",
            "/api/audit",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        return response, json.loads(response.read())


if __name__ == "__main__":
    unittest.main()
