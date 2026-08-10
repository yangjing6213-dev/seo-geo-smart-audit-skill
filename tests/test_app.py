from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
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


class AppRequestTests(unittest.TestCase):
    def test_adds_https_when_scheme_is_omitted(self) -> None:
        url, max_pages = parse_audit_request({"url": "example.com", "max_pages": "25"})
        self.assertEqual("https://example.com", url)
        self.assertEqual(25, max_pages)

    def test_rejects_url_with_credentials(self) -> None:
        with self.assertRaises(AuditRequestError):
            parse_audit_request({"url": "https://name:secret@example.com"})

    def test_rejects_page_limit_outside_public_boundary(self) -> None:
        for value in (0, 301, True, "not-a-number"):
            with self.subTest(value=value), self.assertRaises(AuditRequestError):
                parse_audit_request({"url": "https://example.com", "max_pages": value})

    def test_accepts_300_page_limit(self) -> None:
        _, max_pages = parse_audit_request(
            {"url": "https://example.com", "max_pages": 300}
        )
        self.assertEqual(300, max_pages)

    def test_web_entrypoint_waits_for_user_url_before_showing_report(self) -> None:
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        script = (WEB_DIR / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="audit-form"', html)
        self.assertIn('id="target-url"', html)
        self.assertIn('id="max-pages"', html)
        self.assertIn('value="300"', html)
        self.assertIn('id="report" class="report hidden"', html)
        self.assertIn("输入网址并开始巡检", html)
        self.assertIn("form.addEventListener('submit'", script)
        self.assertIn("fetch('/api/audit'", script)
        self.assertIn("renderReport(data)", script)

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
            audit_site.assert_called_once_with(
                "https://example.com",
                max_pages=10,
                timeout=10,
                delay=0.1,
                max_bytes=5_000_000,
                max_sitemaps=10,
                allow_private=False,
            )
            markdown_report.assert_called_once_with(audit_result)
        finally:
            self._stop_server(server, thread, connection)

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

    def test_readme_documents_direct_public_audit_contract(self) -> None:
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("公开只读巡检接口：`POST /api/audit`", readme)
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
