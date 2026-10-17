import sys
from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from external_evidence import ExternalEvidenceError, summarize_external_evidence  # noqa: E402


class ExternalEvidenceTests(unittest.TestCase):
    def test_summarizes_search_console_and_answer_engine_samples_without_raw_rows(self) -> None:
        package = {
            "schema_version": 1,
            "search_console": {
                "period_start": "2026-10-01",
                "period_end": "2026-10-14",
                "rows": [
                    {
                        "url": "https://example.com/one?private=query",
                        "clicks": 10,
                        "impressions": 100,
                        "position": 4,
                    },
                    {
                        "url": "https://example.com/two",
                        "clicks": 5,
                        "impressions": 100,
                        "position": 8,
                    },
                ],
            },
            "answer_engine_samples": [
                {
                    "engine": "ChatGPT Search",
                    "checked_at": "2026-10-17",
                    "samples": [
                        {"cited_urls": ["https://example.com/one"]},
                        {"cited_urls": ["https://other.example/page"]},
                    ],
                }
            ],
        }

        summary = summarize_external_evidence(package, "https://example.com")

        self.assertEqual(
            {
                "period_start": "2026-10-01",
                "period_end": "2026-10-14",
                "page_rows": 2,
                "clicks": 15,
                "impressions": 200,
                "ctr_percent": 7.5,
                "average_position": 6.0,
            },
            summary["search_console"],
        )
        self.assertEqual(2, summary["answer_engine_samples"][0]["query_samples"])
        self.assertEqual(1, summary["answer_engine_samples"][0]["queries_with_site_citation"])
        self.assertEqual(50.0, summary["answer_engine_samples"][0]["citation_rate_percent"])
        self.assertFalse(summary["affects_score"])
        serialized = str(summary)
        self.assertNotIn("private=query", serialized)
        self.assertNotIn("other.example", serialized)

    def test_rejects_search_console_rows_outside_the_audited_site(self) -> None:
        package = {
            "schema_version": 1,
            "search_console": {
                "period_start": "2026-10-01",
                "period_end": "2026-10-14",
                "rows": [
                    {
                        "url": "https://other.example/page",
                        "clicks": 1,
                        "impressions": 2,
                        "position": 1.0,
                    }
                ],
            },
        }
        with self.assertRaises(ExternalEvidenceError):
            summarize_external_evidence(package, "https://example.com")

    def test_rejects_credentials_and_inconsistent_metrics(self) -> None:
        package = {
            "schema_version": 1,
            "search_console": {
                "period_start": "2026-10-01",
                "period_end": "2026-10-14",
                "rows": [
                    {
                        "url": "https://user:secret@example.com/page",
                        "clicks": 3,
                        "impressions": 2,
                        "position": 1.0,
                    }
                ],
            },
        }
        with self.assertRaises(ExternalEvidenceError):
            summarize_external_evidence(package, "https://example.com")

    def test_treats_explicit_zero_port_as_distinct_origin(self) -> None:
        package = {
            "schema_version": 1,
            "search_console": {
                "period_start": "2026-10-01",
                "period_end": "2026-10-14",
                "rows": [
                    {
                        "url": "https://example.com/page",
                        "clicks": 0,
                        "impressions": 0,
                        "position": None,
                    }
                ],
            },
        }
        with self.assertRaises(ExternalEvidenceError):
            summarize_external_evidence(package, "https://example.com:0")

    def test_rejects_out_of_range_metrics_and_markdown_delimiters(self) -> None:
        package = {
            "schema_version": 1,
            "search_console": {
                "period_start": "2026-10-01",
                "period_end": "2026-10-14",
                "rows": [
                    {
                        "url": "https://example.com/page",
                        "clicks": 1,
                        "impressions": 2**63,
                        "position": 1.0,
                    }
                ],
            },
        }
        with self.assertRaises(ExternalEvidenceError):
            summarize_external_evidence(package, "https://example.com")

        package["search_console"]["rows"][0]["impressions"] = 2
        package["search_console"]["rows"][0]["position"] = 1_000_001
        with self.assertRaises(ExternalEvidenceError):
            summarize_external_evidence(package, "https://example.com")

        package = {
            "schema_version": 1,
            "answer_engine_samples": [
                {
                    "engine": "` malicious markdown",
                    "checked_at": "2026-10-17",
                    "samples": [{"cited_urls": []}],
                }
            ],
        }
        with self.assertRaises(ExternalEvidenceError):
            summarize_external_evidence(package, "https://example.com")

    def test_rejects_raw_query_fields_and_unsupported_schema_versions(self) -> None:
        package = {
            "schema_version": 1,
            "answer_engine_samples": [
                {
                    "engine": "ChatGPT Search",
                    "checked_at": "2026-10-17",
                    "samples": [{"query": "private query", "cited_urls": []}],
                }
            ],
        }
        with self.assertRaises(ExternalEvidenceError):
            summarize_external_evidence(package, "https://example.com")
        with self.assertRaises(ExternalEvidenceError):
            summarize_external_evidence({"schema_version": 2}, "https://example.com")


if __name__ == "__main__":
    unittest.main()
