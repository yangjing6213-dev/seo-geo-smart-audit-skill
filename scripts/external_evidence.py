"""Validate and summarize user-supplied, non-persisted SEO/GEO evidence."""

from __future__ import annotations

from datetime import date
import math
from typing import Any
from urllib.parse import urlsplit


class ExternalEvidenceError(ValueError):
    """Raised when an external evidence package is outside the supported format."""


MAX_SEARCH_CONSOLE_ROWS = 1000
MAX_ANSWER_ENGINE_SAMPLES = 25
MAX_QUERIES_PER_SAMPLE = 500
MAX_CITATIONS_PER_QUERY = 20
MAX_EXTERNAL_EVIDENCE_BYTES = 262_144
MAX_METRIC_COUNT = 2**63 - 1
MAX_AVERAGE_POSITION = 1_000_000


def _require_keys(
    value: dict[str, Any],
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    if not required.issubset(value) or not value.keys() <= required | optional:
        raise ExternalEvidenceError("外部数据格式不受支持。请按 JSON 格式说明整理后重试。")


def _date(value: Any) -> date:
    if (
        not isinstance(value, str)
        or len(value) != 10
        or value[4] != "-"
        or value[7] != "-"
    ):
        raise ExternalEvidenceError("外部数据日期格式无效。")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ExternalEvidenceError("外部数据日期格式无效。") from None


def _origin(value: Any) -> tuple[str, str, int]:
    if not isinstance(value, str):
        raise ExternalEvidenceError("外部数据中的网址无效。")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise ExternalEvidenceError("外部数据中的网址无效。") from None
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ExternalEvidenceError("外部数据中的网址无效。")
    return (
        parsed.scheme.lower(),
        hostname.lower(),
        port if port is not None else (443 if parsed.scheme.lower() == "https" else 80),
    )


def _count(value: Any) -> int:
    if type(value) is not int or value < 0 or value > MAX_METRIC_COUNT:
        raise ExternalEvidenceError("外部数据中的统计数字无效。")
    return value


def _position(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalEvidenceError("外部数据中的平均排名无效。")
    result = float(value)
    if not math.isfinite(result) or result < 0 or result > MAX_AVERAGE_POSITION:
        raise ExternalEvidenceError("外部数据中的平均排名无效。")
    return result


def summarize_external_evidence(package: Any, target_url: str) -> dict[str, Any] | None:
    """Return aggregate-only summaries; never retain page URLs, queries, or source rows."""
    if package is None:
        return None
    if not isinstance(package, dict):
        raise ExternalEvidenceError("外部数据必须是 JSON 对象。")
    _require_keys(package, {"schema_version"}, {"search_console", "answer_engine_samples"})
    if type(package["schema_version"]) is not int or package["schema_version"] != 1:
        raise ExternalEvidenceError("外部数据版本不受支持。")
    if "search_console" not in package and "answer_engine_samples" not in package:
        raise ExternalEvidenceError("外部数据至少需要包含一种数据来源。")

    target_origin = _origin(target_url)
    result: dict[str, Any] = {
        "search_console": None,
        "answer_engine_samples": [],
        "affects_score": False,
        "raw_rows_retained": False,
    }

    search_console = package.get("search_console")
    if search_console is not None:
        if not isinstance(search_console, dict):
            raise ExternalEvidenceError("Search Console 数据格式无效。")
        _require_keys(search_console, {"period_start", "period_end", "rows"})
        period_start = _date(search_console["period_start"])
        period_end = _date(search_console["period_end"])
        rows = search_console["rows"]
        if period_end < period_start or not isinstance(rows, list) or not 1 <= len(rows) <= MAX_SEARCH_CONSOLE_ROWS:
            raise ExternalEvidenceError("Search Console 数据范围或行数无效。")

        clicks_total = 0
        impressions_total = 0
        position_weighted_total = 0.0
        position_impressions = 0
        for row in rows:
            if not isinstance(row, dict):
                raise ExternalEvidenceError("Search Console 页面数据格式无效。")
            _require_keys(row, {"url", "clicks", "impressions", "position"})
            if _origin(row["url"]) != target_origin:
                raise ExternalEvidenceError("Search Console 页面必须属于本次检查的网站。")
            clicks = _count(row["clicks"])
            impressions = _count(row["impressions"])
            position = _position(row["position"])
            if clicks > impressions or (impressions > 0 and position is None):
                raise ExternalEvidenceError("Search Console 指标之间不一致。")
            clicks_total += clicks
            impressions_total += impressions
            if impressions and position is not None:
                position_weighted_total += position * impressions
                position_impressions += impressions

        result["search_console"] = {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "page_rows": len(rows),
            "clicks": clicks_total,
            "impressions": impressions_total,
            "ctr_percent": round(clicks_total * 100 / impressions_total, 2) if impressions_total else 0.0,
            "average_position": (
                round(position_weighted_total / position_impressions, 2)
                if position_impressions
                else None
            ),
        }

    answer_samples = package.get("answer_engine_samples", [])
    if not isinstance(answer_samples, list) or len(answer_samples) > MAX_ANSWER_ENGINE_SAMPLES:
        raise ExternalEvidenceError("答案引擎抽样数据格式或数量无效。")
    for source in answer_samples:
        if not isinstance(source, dict):
            raise ExternalEvidenceError("答案引擎抽样数据格式无效。")
        _require_keys(source, {"engine", "checked_at", "samples"})
        engine = source["engine"]
        if (
            not isinstance(engine, str)
            or not engine.strip()
            or len(engine.strip()) > 80
            or "`" in engine
            or any(ord(character) < 32 for character in engine)
        ):
            raise ExternalEvidenceError("答案引擎名称无效。")
        checked_at = _date(source["checked_at"])
        samples = source["samples"]
        if not isinstance(samples, list) or not 1 <= len(samples) <= MAX_QUERIES_PER_SAMPLE:
            raise ExternalEvidenceError("答案引擎抽样数量无效。")

        cited_count = 0
        for sample in samples:
            if not isinstance(sample, dict):
                raise ExternalEvidenceError("答案引擎抽样记录格式无效。")
            _require_keys(sample, {"cited_urls"})
            cited_urls = sample["cited_urls"]
            if not isinstance(cited_urls, list) or len(cited_urls) > MAX_CITATIONS_PER_QUERY:
                raise ExternalEvidenceError("答案引擎引用列表无效。")
            if any(_origin(url) == target_origin for url in cited_urls):
                cited_count += 1

        result["answer_engine_samples"].append(
            {
                "engine": engine.strip(),
                "checked_at": checked_at.isoformat(),
                "query_samples": len(samples),
                "queries_with_site_citation": cited_count,
                "citation_rate_percent": round(cited_count * 100 / len(samples), 2),
            }
        )

    if result["search_console"] is None and not result["answer_engine_samples"]:
        raise ExternalEvidenceError("外部数据至少需要包含一种有效数据来源。")
    return result
