#!/usr/bin/env python3
"""Render a self-contained HTML artifact for an SEO/GEO audit."""

from __future__ import annotations

from html import escape
import json
from typing import Any
from urllib.parse import urlsplit


CREATOR_NAME = "ENHE AI工作室"
CREATOR_URL = "https://www.enhe-tech.com.cn"

SEVERITY_LABELS = {
    "critical": "严重",
    "high": "高",
    "medium": "中",
    "low": "低",
    "info": "信息",
}

STATUS_LABELS = {
    "verified": "已验证",
    "render_required": "待渲染验证",
    "external_data_required": "待外部数据",
    "hypothesis": "待调查",
}


def _text(value: Any) -> str:
    return escape("" if value is None else str(value), quote=True)


def _safe_href(value: Any) -> str:
    candidate = "" if value is None else str(value)
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return "#"
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return "#"
    return escape(candidate, quote=True)


def _json_evidence(value: Any) -> str:
    return escape(json.dumps(value, ensure_ascii=False, indent=2), quote=False)


def _finding_card(item: dict[str, Any]) -> str:
    severity = str(item.get("severity", "info")).lower()
    if severity not in SEVERITY_LABELS:
        severity = "info"
    status = str(item.get("status", "hypothesis"))
    finding_id = _text(item.get("id", "-"))
    return f"""
        <article class="finding reveal" data-severity="{_text(severity)}">
          <div class="finding-head">
            <div class="finding-id">{finding_id}</div>
            <div class="finding-tags">
              <span class="tag severity-{_text(severity)}">{_text(SEVERITY_LABELS[severity])}</span>
              <span class="tag tag-neutral">{_text(STATUS_LABELS.get(status, status))}</span>
            </div>
          </div>
          <h3>{_text(item.get("issue", "未命名问题"))}</h3>
          <p class="finding-category">{_text(item.get("category", "未分类"))}</p>
          <div class="finding-grid">
            <div>
              <span class="field-label">最小修复</span>
              <p>{_text(item.get("action", "暂无建议"))}</p>
            </div>
            <div>
              <span class="field-label">验收方法</span>
              <p>{_text(item.get("verification", "暂无验收方法"))}</p>
            </div>
          </div>
          <details class="evidence">
            <summary>查看当前证据</summary>
            <pre>{_json_evidence(item.get("evidence"))}</pre>
          </details>
        </article>
    """


def _strength_item(item: dict[str, Any]) -> str:
    return f"""
        <details class="strength reveal">
          <summary>
            <span class="strength-id">{_text(item.get("id", "-"))}</span>
            <span class="strength-title">{_text(item.get("title", "已验证能力"))}</span>
            <span class="strength-state">已验证</span>
          </summary>
          <div class="strength-body">
            <p>{_text(item.get("value", ""))}</p>
            <div class="strength-meta">类别：{_text(item.get("category", "未分类"))}</div>
            <pre>{_json_evidence(item.get("evidence"))}</pre>
          </div>
        </details>
    """


def _recommendation_item(item: dict[str, Any], index: int) -> str:
    return f"""
        <article class="recommendation reveal">
          <div class="recommendation-step">{index:02d}</div>
          <div>
            <div class="recommendation-priority">{_text(item.get("priority", "P2"))}</div>
            <h3>{_text(item.get("title", "后续优化"))}</h3>
            <p>{_text(item.get("reason", ""))}</p>
            <div class="next-step"><span>下一步</span>{_text(item.get("next_step", ""))}</div>
          </div>
        </article>
    """


def _page_row(page: dict[str, Any]) -> str:
    raw_url = page.get("url", "")
    status = page.get("status")
    status_text = "-" if status is None else str(status)
    page_type = "HTML" if page.get("is_html") else "非 HTML"
    state = "失败" if page.get("error") else ("已阻止" if page.get("robots_blocked") else "完成")
    search = f"{raw_url} {status_text} {page_type} {state}".lower()
    return f"""
        <tr data-page-row data-search="{_text(search)}">
          <td><a href="{_safe_href(raw_url)}" target="_blank" rel="noopener noreferrer">{_text(raw_url)}</a></td>
          <td><span class="http-status">{_text(status_text)}</span></td>
          <td>{_text(page_type)}</td>
          <td>{_text(state)}</td>
        </tr>
    """


def _external_evidence_section(evidence: Any) -> str:
    if not isinstance(evidence, dict):
        return ""
    sections: list[str] = []
    search_console = evidence.get("search_console")
    if isinstance(search_console, dict):
        position = search_console.get("average_position")
        sections.append(
            f"""
            <article class="summary-card">
              <span class="label">Search Console · {_text(search_console.get('period_start'))} 至 {_text(search_console.get('period_end'))}</span>
              <strong>{_text(search_console.get('clicks'))} / {_text(search_console.get('impressions'))}</strong>
              <p>点击 / 展示 · 汇总点击率 {_text(search_console.get('ctr_percent'))}% · 按展示加权平均排名 {_text(position if position is not None else '未提供')}</p>
            </article>
            """
        )
    for item in evidence.get("answer_engine_samples", []):
        if not isinstance(item, dict):
            continue
        sections.append(
            f"""
            <article class="summary-card">
              <span class="label">答案引擎抽样 · {_text(item.get('checked_at'))}</span>
              <strong>{_text(item.get('queries_with_site_citation'))} / {_text(item.get('query_samples'))}</strong>
              <p>{_text(item.get('engine'))} · 抽样引用率 {_text(item.get('citation_rate_percent'))}%</p>
            </article>
            """
        )
    if not sections:
        return ""
    return f"""
    <section class="report-section" aria-labelledby="external-evidence-title">
      <div class="section-head">
        <div><div class="section-index">Supplemental data</div><h2 id="external-evidence-title">外部数据补充</h2></div>
        <p class="section-intro">由用户导入的聚合数据；原始行和查询内容不会写入报告，也不参与评分。</p>
      </div>
      <div class="summary-grid">{''.join(sections)}</div>
    </section>
    """


def _browser_rendering_section(rendering: Any, pages: list[dict[str, Any]]) -> str:
    if not isinstance(rendering, dict) or not rendering.get("enabled"):
        return ""
    page_cards: list[str] = []
    field_labels = {
        "title": "页面标题",
        "meta_description": "摘要描述",
        "canonical": "规范网址",
        "html_lang": "页面语言",
        "robots_directive": "抓取指令",
        "h1": "一级标题",
        "json_ld_static_count": "结构化数据块",
    }
    for index, page in enumerate(pages, start=1):
        observation = page.get("browser_render")
        if not isinstance(observation, dict):
            continue
        differences = observation.get("differences", [])
        difference_labels = [field_labels.get(item, str(item)) for item in differences]
        title = observation.get("title") or "未检测到页面标题"
        description = observation.get("meta_description") or "未检测到摘要描述"
        h1 = "、".join(str(item) for item in observation.get("h1", [])) or "未检测到一级标题"
        error_markup = (
            f"<p>{_text(observation.get('error'))}</p>" if observation.get("error") else ""
        )
        page_cards.append(
            f"""
            <article class="summary-card">
              <span class="label">浏览器抽样页面 {index} · {_text(observation.get('status', 'unknown'))} · HTTP {_text(observation.get('http_status', '-'))}</span>
              <strong>{_text(title)}</strong>
              <p>摘要描述：{_text(description)}</p>
              <p>一级标题：{_text(h1)}</p>
              <p>与静态抓取不同：{_text('、'.join(difference_labels) if difference_labels else '未发现差异')}</p>
              {error_markup}
            </article>
            """
        )
    summary_card = f"""
      <article class="summary-card">
        <span class="label">浏览器检查汇总</span>
        <strong>{_text(rendering.get('rendered_pages', 0))} / {_text(rendering.get('sampled_pages', 0))}</strong>
        <p>已渲染 / 抽样页面；拦截请求 {_text(rendering.get('blocked_requests', 0))} 个；此补充观察不参与评分。</p>
      </article>
    """
    return f"""
    <section class="report-section" aria-labelledby="browser-rendering-title">
      <div class="section-head">
        <div><div class="section-index">Rendered evidence</div><h2 id="browser-rendering-title">浏览器渲染观察</h2></div>
        <p class="section-intro">最多抽查 10 页；只允许同站公开只读请求。原始渲染 HTML 不保留，观察结果不参与评分。</p>
      </div>
      <div class="summary-grid">{summary_card}{''.join(page_cards)}</div>
    </section>
    """


def html_report(audit: dict[str, Any]) -> str:
    """Return a complete, offline-capable HTML report for an audit result."""
    meta = audit.get("meta", {})
    summary = audit.get("summary", {})
    score = audit.get("score", {})
    findings = list(audit.get("findings", []))
    strengths = list(audit.get("strengths", []))
    recommendations = list(audit.get("recommendations", []))
    pages = list(audit.get("pages", []))
    limitations = list(meta.get("limitations", []))
    analysis_scope = summary.get("analysis_scope", {})
    external_evidence_markup = _external_evidence_section(audit.get("external_evidence"))
    browser_rendering_markup = _browser_rendering_section(
        audit.get("browser_rendering"), pages
    )

    overall = max(0, min(100, int(score.get("overall", 0) or 0)))
    evidence_coverage = max(0, min(100, int(score.get("evidence_coverage", 0) or 0)))
    target = str(meta.get("target", ""))
    hostname = urlsplit(target).hostname or target or "待审计站点"

    severity_counts = {
        key: sum(1 for item in findings if str(item.get("severity", "info")).lower() == key)
        for key in SEVERITY_LABELS
    }
    verified_count = sum(1 for item in findings if item.get("status") == "verified")
    pending_count = len(findings) - verified_count

    finding_markup = "".join(_finding_card(item) for item in findings)
    if not finding_markup:
        finding_markup = '<div class="empty-state">本次没有发现需要列出的审计问题。</div>'

    strength_markup = "".join(_strength_item(item) for item in strengths)
    if not strength_markup:
        strength_markup = '<div class="empty-state">当前证据尚未形成可确认的优势项。</div>'

    recommendation_markup = "".join(
        _recommendation_item(item, index) for index, item in enumerate(recommendations, start=1)
    )
    if not recommendation_markup:
        recommendation_markup = '<div class="empty-state">当前没有额外行动建议。</div>'

    page_markup = "".join(_page_row(page) for page in pages)
    if not page_markup:
        page_markup = '<tr><td colspan="4">没有已抓取页面记录。</td></tr>'

    limitation_markup = "".join(f"<li>{_text(item)}</li>" for item in limitations)
    if not limitation_markup:
        limitation_markup = "<li>本次报告未声明额外限制。</li>"

    finished_at = meta.get("finished_at", "-")
    engine_version = meta.get("engine_version", "-")
    score_label = score.get("label", "待评估")
    score_summary = score.get("summary", "当前报告只陈述已有证据。")
    score_method = score.get("method", "未提供评分方法。")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <meta name="description" content="{_text(hostname)} SEO/GEO 证据化巡检报告">
  <title>{_text(hostname)} SEO/GEO 巡检报告</title>
  <style>
    :root {{
      --paper: #f4f5f1;
      --surface: #ffffff;
      --ink: #121713;
      --muted: #626a63;
      --line: #d8ddd7;
      --line-strong: #b9c1ba;
      --green: #0f6b4f;
      --green-soft: #e4f1eb;
      --blue: #2358a5;
      --blue-soft: #e8eef8;
      --amber: #9a5a00;
      --amber-soft: #f8ecd6;
      --red: #a52d35;
      --red-soft: #f8e7e8;
      --shadow: 0 18px 60px rgba(24, 36, 28, 0.08);
      --radius: 6px;
      --content: 1180px;
    }}

    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", Arial, sans-serif;
      font-size: 15px;
      line-height: 1.7;
      letter-spacing: 0;
      overflow-x: clip;
    }}
    a {{ color: inherit; text-decoration-thickness: 1px; text-underline-offset: 3px; }}
    button, input {{ font: inherit; letter-spacing: 0; }}
    button:focus-visible, input:focus-visible, a:focus-visible, summary:focus-visible {{
      outline: 3px solid rgba(35, 88, 165, 0.28);
      outline-offset: 3px;
    }}
    [hidden] {{ display: none !important; }}

    .topbar {{
      position: sticky;
      top: 0;
      z-index: 20;
      border-bottom: 1px solid rgba(185, 193, 186, 0.8);
      background: rgba(244, 245, 241, 0.94);
      backdrop-filter: blur(14px);
    }}
    .topbar-inner {{
      width: min(calc(100% - 40px), var(--content));
      min-height: 58px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
    }}
    .creator {{ display: inline-flex; align-items: center; gap: 10px; text-decoration: none; font-weight: 700; }}
    .creator-mark {{
      width: 30px;
      height: 30px;
      display: grid;
      place-items: center;
      border: 1px solid var(--ink);
      border-radius: 50%;
      font-size: 11px;
      line-height: 1;
      background: var(--ink);
      color: #fff;
    }}
    .topnav {{ display: flex; gap: 18px; overflow-x: auto; scrollbar-width: none; }}
    .topnav::-webkit-scrollbar {{ display: none; }}
    .topnav a {{ color: var(--muted); text-decoration: none; white-space: nowrap; font-size: 13px; }}
    .topnav a:hover {{ color: var(--green); }}

    main {{ width: min(calc(100% - 40px), var(--content)); margin: 0 auto; }}
    .hero {{
      min-height: 520px;
      padding: 88px 0 64px;
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.6fr);
      align-items: end;
      gap: 64px;
      border-bottom: 1px solid var(--line-strong);
    }}
    .eyebrow {{ color: var(--green); font-size: 12px; font-weight: 800; text-transform: uppercase; }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{
      max-width: 850px;
      margin: 18px 0 24px;
      font-size: clamp(38px, 6vw, 78px);
      line-height: 1.06;
      font-weight: 760;
      overflow-wrap: anywhere;
    }}
    .hero-summary {{ max-width: 760px; color: #3d453e; font-size: 18px; line-height: 1.8; }}
    .target-link {{
      display: inline-block;
      max-width: 100%;
      margin-top: 20px;
      color: var(--blue);
      font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
      overflow-wrap: anywhere;
    }}
    .score-panel {{ display: grid; justify-items: center; gap: 18px; }}
    .score-ring {{ width: 196px; height: 196px; transform: rotate(-90deg); }}
    .score-track, .score-value {{ fill: none; stroke-width: 7; }}
    .score-track {{ stroke: var(--line); }}
    .score-value {{ stroke: var(--green); stroke-linecap: round; transition: stroke-dasharray 1.1s ease; }}
    .score-number {{
      margin-top: -143px;
      min-width: 150px;
      text-align: center;
      font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
      font-size: 54px;
      font-weight: 760;
      line-height: 1;
    }}
    .score-number span {{ font-size: 17px; color: var(--muted); }}
    .score-label {{ margin-top: 52px; color: var(--muted); }}

    .metric-band {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      border-bottom: 1px solid var(--line-strong);
    }}
    .metric {{ padding: 26px 22px; border-right: 1px solid var(--line); }}
    .metric:first-child {{ padding-left: 0; }}
    .metric:last-child {{ border-right: 0; }}
    .metric-value {{ display: block; font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: 30px; font-weight: 760; }}
    .metric-label {{ color: var(--muted); font-size: 12px; }}

    .report-section {{ padding: 86px 0; border-bottom: 1px solid var(--line-strong); }}
    .section-head {{
      display: grid;
      grid-template-columns: minmax(0, 0.65fr) minmax(280px, 0.35fr);
      gap: 56px;
      align-items: end;
      margin-bottom: 38px;
    }}
    .section-index {{ color: var(--green); font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: 12px; }}
    .section-head h2 {{ margin: 8px 0 0; font-size: clamp(30px, 4vw, 48px); line-height: 1.18; }}
    .section-intro {{ margin: 0; color: var(--muted); }}

    .filter-bar {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px; }}
    .filter-button {{
      min-height: 40px;
      padding: 8px 14px;
      border: 1px solid var(--line-strong);
      border-radius: 999px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      transition: color 160ms ease, background-color 160ms ease, border-color 160ms ease, transform 160ms ease;
    }}
    .filter-button:hover {{ color: var(--ink); border-color: var(--ink); transform: translateY(-1px); }}
    .filter-button[aria-pressed="true"] {{ color: #fff; border-color: var(--ink); background: var(--ink); }}

    .finding-list {{ display: grid; gap: 14px; }}
    .finding {{
      padding: 26px;
      border: 1px solid var(--line);
      border-left: 4px solid var(--line-strong);
      border-radius: var(--radius);
      background: var(--surface);
      box-shadow: 0 1px 0 rgba(18, 23, 19, 0.03);
      transition: transform 180ms ease, box-shadow 180ms ease;
    }}
    .finding:hover {{ transform: translateY(-2px); box-shadow: var(--shadow); }}
    .finding[data-severity="critical"] {{ border-left-color: var(--red); }}
    .finding[data-severity="high"] {{ border-left-color: var(--red); }}
    .finding[data-severity="medium"] {{ border-left-color: var(--amber); }}
    .finding[data-severity="low"] {{ border-left-color: var(--blue); }}
    .finding[data-severity="info"] {{ border-left-color: var(--green); }}
    .finding-head {{ display: flex; justify-content: space-between; gap: 18px; align-items: center; }}
    .finding-id, .strength-id {{ font-family: ui-monospace, "Cascadia Code", Consolas, monospace; color: var(--muted); font-size: 12px; }}
    .finding-tags {{ display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }}
    .tag {{ padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: 700; }}
    .severity-critical, .severity-high {{ color: var(--red); background: var(--red-soft); }}
    .severity-medium {{ color: var(--amber); background: var(--amber-soft); }}
    .severity-low {{ color: var(--blue); background: var(--blue-soft); }}
    .severity-info {{ color: var(--green); background: var(--green-soft); }}
    .tag-neutral {{ color: #4d554e; background: #edf0ed; }}
    .finding h3 {{ margin: 16px 0 6px; max-width: 900px; font-size: 21px; line-height: 1.45; }}
    .finding-category {{ color: var(--muted); font-size: 12px; }}
    .finding-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; padding-top: 18px; border-top: 1px solid var(--line); }}
    .finding-grid p {{ margin-bottom: 0; color: #3d453e; }}
    .field-label {{ display: block; margin-bottom: 6px; color: var(--muted); font-size: 11px; font-weight: 800; }}

    details {{ border-radius: var(--radius); }}
    summary {{ cursor: pointer; }}
    .evidence {{ margin-top: 18px; border-top: 1px solid var(--line); padding-top: 14px; }}
    .evidence summary {{ color: var(--blue); font-weight: 700; }}
    pre {{
      max-width: 100%;
      overflow: auto;
      margin: 14px 0 0;
      padding: 16px;
      border: 1px solid #dfe3df;
      border-radius: 4px;
      background: #f7f8f6;
      color: #263028;
      font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
      font-size: 12px;
      line-height: 1.6;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }}

    .strength-list {{ border-top: 1px solid var(--line-strong); }}
    .strength {{ border-bottom: 1px solid var(--line-strong); }}
    .strength summary {{
      min-height: 72px;
      display: grid;
      grid-template-columns: 74px minmax(0, 1fr) 90px;
      align-items: center;
      gap: 18px;
      list-style: none;
    }}
    .strength summary::-webkit-details-marker {{ display: none; }}
    .strength-title {{ font-size: 17px; font-weight: 700; }}
    .strength-state {{ color: var(--green); text-align: right; font-size: 12px; }}
    .strength-body {{ padding: 0 0 24px 92px; max-width: 920px; }}
    .strength-body p {{ color: #3d453e; }}
    .strength-meta {{ color: var(--muted); font-size: 12px; }}

    .recommendation-list {{ display: grid; gap: 0; }}
    .recommendation {{
      display: grid;
      grid-template-columns: 74px minmax(0, 1fr);
      gap: 22px;
      padding: 30px 0;
      border-top: 1px solid var(--line);
    }}
    .recommendation:last-child {{ border-bottom: 1px solid var(--line); }}
    .recommendation-step {{ font-family: ui-monospace, "Cascadia Code", Consolas, monospace; color: var(--green); font-size: 20px; }}
    .recommendation-priority {{ color: var(--muted); font-size: 11px; font-weight: 800; }}
    .recommendation h3 {{ margin: 6px 0 8px; font-size: 22px; }}
    .recommendation p {{ color: var(--muted); }}
    .next-step {{ padding: 12px 14px; border-left: 3px solid var(--green); background: var(--green-soft); }}
    .next-step span {{ margin-right: 10px; font-weight: 800; }}

    .page-tools {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: end;
      gap: 20px;
      margin-bottom: 20px;
    }}
    .page-search label {{ display: block; margin-bottom: 6px; color: var(--muted); font-size: 12px; font-weight: 700; }}
    .page-search input {{
      width: 100%;
      min-height: 46px;
      padding: 10px 13px;
      border: 1px solid var(--line-strong);
      border-radius: 4px;
      background: var(--surface);
      color: var(--ink);
    }}
    .page-count {{ color: var(--muted); font-size: 13px; }}
    .table-wrap {{ overflow: auto; border-top: 1px solid var(--line-strong); border-bottom: 1px solid var(--line-strong); background: var(--surface); }}
    table {{ width: 100%; border-collapse: collapse; min-width: 760px; }}
    th, td {{ padding: 13px 14px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ position: sticky; top: 58px; z-index: 2; background: #eef1ed; color: #4b534c; font-size: 11px; }}
    td:first-child {{ width: 70%; font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: 12px; overflow-wrap: anywhere; }}
    .http-status {{ font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-weight: 750; }}

    .method-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 48px; }}
    .method-grid h3 {{ font-size: 18px; }}
    .method-grid p, .method-grid li {{ color: var(--muted); }}
    .method-grid ul {{ padding-left: 20px; }}
    .meta-list {{ display: grid; gap: 0; border-top: 1px solid var(--line); }}
    .meta-row {{ display: grid; grid-template-columns: 150px minmax(0, 1fr); gap: 18px; padding: 12px 0; border-bottom: 1px solid var(--line); }}
    .meta-row dt {{ color: var(--muted); }}
    .meta-row dd {{ margin: 0; overflow-wrap: anywhere; }}
    .empty-state {{ padding: 28px; border: 1px solid var(--line); background: var(--surface); color: var(--muted); }}

    footer {{ width: min(calc(100% - 40px), var(--content)); margin: 0 auto; padding: 34px 0 46px; display: flex; justify-content: space-between; gap: 24px; color: var(--muted); font-size: 12px; }}
    footer a {{ color: var(--ink); }}

    .motion-ready .reveal {{ opacity: 0; transform: translateY(14px); }}
    .motion-ready .reveal.is-visible {{ opacity: 1; transform: translateY(0); transition: opacity 500ms ease, transform 500ms ease; }}

    @media (max-width: 860px) {{
      .topbar-inner {{ width: min(calc(100% - 28px), var(--content)); }}
      .creator span:last-child {{ display: none; }}
      main, footer {{ width: min(calc(100% - 28px), var(--content)); }}
      .hero {{ min-height: auto; padding: 58px 0 44px; grid-template-columns: 1fr; gap: 38px; align-items: start; }}
      h1 {{ font-size: clamp(38px, 13vw, 60px); }}
      .score-panel {{ justify-items: start; }}
      .metric-band {{ grid-template-columns: repeat(2, 1fr); }}
      .metric {{ border-bottom: 1px solid var(--line); }}
      .metric:nth-child(even) {{ border-right: 0; }}
      .metric:first-child {{ padding-left: 22px; }}
      .metric:last-child {{ grid-column: 1 / -1; }}
      .report-section {{ padding: 62px 0; }}
      .section-head {{ grid-template-columns: 1fr; gap: 16px; }}
      .finding-grid, .method-grid {{ grid-template-columns: 1fr; gap: 22px; }}
      .strength summary {{ grid-template-columns: 58px minmax(0, 1fr); }}
      .strength-state {{ display: none; }}
      .strength-body {{ padding-left: 76px; }}
      .page-tools {{ grid-template-columns: 1fr; }}
      footer {{ flex-direction: column; }}
    }}

    @media (max-width: 480px) {{
      .topnav {{ gap: 14px; }}
      .topnav a:nth-child(n+4) {{ display: none; }}
      .hero-summary {{ font-size: 16px; }}
      .finding {{ padding: 20px; }}
      .finding-head {{ align-items: flex-start; }}
      .finding-tags {{ justify-content: flex-start; }}
      .recommendation {{ grid-template-columns: 48px minmax(0, 1fr); gap: 14px; }}
      .meta-row {{ grid-template-columns: 1fr; gap: 2px; }}
    }}

    @media print {{
      .topbar, .filter-bar, .page-tools {{ display: none !important; }}
      body {{ background: #fff; }}
      main, footer {{ width: 100%; }}
      .hero {{ min-height: auto; padding-top: 20px; }}
      .report-section {{ break-inside: avoid; }}
      .finding, .strength {{ break-inside: avoid; box-shadow: none; }}
      .motion-ready .reveal {{ opacity: 1 !important; transform: none !important; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      html {{ scroll-behavior: auto; }}
      *, *::before, *::after {{ animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }}
      .motion-ready .reveal {{ opacity: 1; transform: none; }}
    }}
  </style>
</head>
<body data-report-version="1.0">
  <header class="topbar">
    <div class="topbar-inner">
      <a class="creator" href="{CREATOR_URL}" target="_blank" rel="noopener noreferrer" aria-label="访问 ENHE AI工作室官网">
        <span class="creator-mark" aria-hidden="true">EN</span>
        <span>{CREATOR_NAME}</span>
      </a>
      <nav class="topnav" aria-label="报告章节">
        <a href="#overview">总览</a>
        <a href="#findings">问题</a>
        <a href="#strengths">优势</a>
        <a href="#recommendations">行动</a>
        <a href="#pages">页面</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="hero" id="overview" aria-labelledby="report-title">
      <div>
        <div class="eyebrow">Independent Site SEO / GEO Audit</div>
        <h1 id="report-title">{_text(hostname)}<br>巡检报告</h1>
        <p class="hero-summary">{_text(score_summary)}</p>
        <a class="target-link" href="{_safe_href(target)}" target="_blank" rel="noopener noreferrer">{_text(target)}</a>
      </div>
      <div class="score-panel" aria-label="综合评分 {_text(overall)} 分">
        <svg class="score-ring" viewBox="0 0 120 120" role="img" aria-label="综合评分 {_text(overall)} 分">
          <circle class="score-track" cx="60" cy="60" r="52" pathLength="100"></circle>
          <circle class="score-value" cx="60" cy="60" r="52" pathLength="100" data-score-ring data-score="{overall}" stroke-dasharray="{overall} 100"></circle>
        </svg>
        <div class="score-number"><strong data-count="{overall}">{overall}</strong><span>/100</span></div>
        <div class="score-label">{_text(score_label)}</div>
      </div>
    </section>

    <section class="metric-band" aria-label="巡检关键指标">
      <div class="metric"><span class="metric-value" data-count="{evidence_coverage}">{evidence_coverage}</span><span class="metric-label">检查证据完备度 %</span></div>
      <div class="metric"><span class="metric-value" data-count="{_text(summary.get('pages_crawled', 0))}">{_text(summary.get('pages_crawled', 0))}</span><span class="metric-label">已抓取页面</span></div>
      <div class="metric"><span class="metric-value" data-count="{len(strengths)}">{len(strengths)}</span><span class="metric-label">已验证优势</span></div>
      <div class="metric"><span class="metric-value" data-count="{verified_count}">{verified_count}</span><span class="metric-label">已验证问题</span></div>
      <div class="metric"><span class="metric-value" data-count="{pending_count}">{pending_count}</span><span class="metric-label">待补证据</span></div>
    </section>
    {external_evidence_markup}
    {browser_rendering_markup}

    <section class="report-section" id="findings" aria-labelledby="findings-title">
      <div class="section-head reveal">
        <div><div class="section-index">01 / Findings</div><h2 id="findings-title">优先问题</h2></div>
        <p class="section-intro">按严重程度和证据状态分层。只有已验证问题计入扣分，待渲染或外部数据项只保留为取证任务。</p>
      </div>
      <div class="filter-bar" role="group" aria-label="按严重程度筛选问题">
        <button class="filter-button" type="button" data-filter="all" aria-pressed="true">全部 {len(findings)}</button>
        <button class="filter-button" type="button" data-filter="critical" aria-pressed="false">严重 {severity_counts['critical']}</button>
        <button class="filter-button" type="button" data-filter="high" aria-pressed="false">高 {severity_counts['high']}</button>
        <button class="filter-button" type="button" data-filter="medium" aria-pressed="false">中 {severity_counts['medium']}</button>
        <button class="filter-button" type="button" data-filter="low" aria-pressed="false">低 {severity_counts['low']}</button>
        <button class="filter-button" type="button" data-filter="info" aria-pressed="false">信息 {severity_counts['info']}</button>
      </div>
      <div class="finding-list" aria-live="polite">{finding_markup}</div>
    </section>

    <section class="report-section" id="strengths" aria-labelledby="strengths-title">
      <div class="section-head reveal">
        <div><div class="section-index">02 / Strengths</div><h2 id="strengths-title">已经具备的能力</h2></div>
        <p class="section-intro">这些项目由当前抓取证据直接支持。后续修复应将它们作为回归保护线。</p>
      </div>
      <div class="strength-list">{strength_markup}</div>
    </section>

    <section class="report-section" id="recommendations" aria-labelledby="recommendations-title">
      <div class="section-head reveal">
        <div><div class="section-index">03 / Actions</div><h2 id="recommendations-title">建议行动</h2></div>
        <p class="section-intro">按风险和证据缺口安排最小修复，不把一次巡检描述成持续监控。</p>
      </div>
      <div class="recommendation-list">{recommendation_markup}</div>
    </section>

    <section class="report-section" id="pages" aria-labelledby="pages-title">
      <div class="section-head reveal">
        <div><div class="section-index">04 / Coverage</div><h2 id="pages-title">抓取覆盖</h2></div>
        <p class="section-intro">页面记录用于复核抓取范围，不等同于搜索引擎已收录证明。</p>
      </div>
      <div class="page-tools">
        <div class="page-search">
          <label for="page-search">筛选已抓取页面</label>
          <input id="page-search" type="search" placeholder="输入 URL、状态码或页面类型" autocomplete="off">
        </div>
        <div class="page-count" aria-live="polite"><span id="visible-page-count">{len(pages)}</span> / {len(pages)} 个页面</div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th scope="col">URL</th><th scope="col">HTTP</th><th scope="col">类型</th><th scope="col">状态</th></tr></thead>
          <tbody>{page_markup}</tbody>
        </table>
      </div>
    </section>

    <section class="report-section" id="methodology" aria-labelledby="methodology-title">
      <div class="section-head reveal">
        <div><div class="section-index">05 / Evidence</div><h2 id="methodology-title">证据与边界</h2></div>
        <p class="section-intro">报告严格区分已验证事实、待渲染检查、外部数据需求和调查假设。</p>
      </div>
      <div class="method-grid">
        <div>
          <h3>报告信息</h3>
          <dl class="meta-list">
            <div class="meta-row"><dt>目标站点</dt><dd>{_text(target)}</dd></div>
            <div class="meta-row"><dt>完成时间</dt><dd>{_text(finished_at)}</dd></div>
            <div class="meta-row"><dt>规则引擎</dt><dd>{_text(engine_version)}</dd></div>
            <div class="meta-row"><dt>抓取上限</dt><dd>{_text(meta.get('max_pages', '-'))}</dd></div>
            <div class="meta-row"><dt>User-Agent</dt><dd>{_text(meta.get('user_agent', '-'))}</dd></div>
            <div class="meta-row"><dt>规范分析页</dt><dd>{_text(analysis_scope.get('canonical_indexable_pages', '-'))}；排除重定向 {_text(analysis_scope.get('redirect_aliases_excluded', 0))}、noindex {_text(analysis_scope.get('noindex_excluded', 0))}、非规范 {_text(analysis_scope.get('canonical_away_excluded', 0))}</dd></div>
          </dl>
        </div>
        <div>
          <h3>评分方法与限制</h3>
          <p>{_text(score_method)}</p>
          <ul>{limitation_markup}</ul>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div>报告由 <a href="{CREATOR_URL}" target="_blank" rel="noopener noreferrer">{CREATOR_NAME}</a> 生成</div>
    <a href="{CREATOR_URL}" target="_blank" rel="noopener noreferrer">{CREATOR_URL}</a>
  </footer>

  <script>
    (() => {{
      const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const root = document.documentElement;

      if (!reduceMotion) {{
        root.classList.add('motion-ready');
        const reveals = Array.from(document.querySelectorAll('.reveal'));
        const observer = new IntersectionObserver((entries) => {{
          entries.forEach((entry) => {{
            if (entry.isIntersecting) {{
              entry.target.classList.add('is-visible');
              observer.unobserve(entry.target);
            }}
          }});
        }}, {{ threshold: 0.08 }});
        reveals.forEach((element) => observer.observe(element));

        document.querySelectorAll('[data-count]').forEach((element) => {{
          const target = Number(element.dataset.count);
          if (!Number.isFinite(target)) return;
          const duration = 700;
          const started = performance.now();
          const step = (now) => {{
            const progress = Math.min(1, (now - started) / duration);
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = String(Math.round(target * eased));
            if (progress < 1) requestAnimationFrame(step);
          }};
          requestAnimationFrame(step);
        }});

        const scoreRing = document.querySelector('[data-score-ring]');
        if (scoreRing) {{
          const score = Number(scoreRing.dataset.score) || 0;
          scoreRing.style.strokeDasharray = '0 100';
          requestAnimationFrame(() => {{ scoreRing.style.strokeDasharray = `${{score}} 100`; }});
        }}
      }}

      const filterButtons = Array.from(document.querySelectorAll('[data-filter]'));
      const findingCards = Array.from(document.querySelectorAll('[data-severity]'));
      filterButtons.forEach((button) => {{
        button.addEventListener('click', () => {{
          const filter = button.dataset.filter;
          filterButtons.forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button)));
          findingCards.forEach((card) => {{
            card.hidden = filter !== 'all' && card.dataset.severity !== filter;
          }});
        }});
      }});

      const search = document.querySelector('#page-search');
      const pageRows = Array.from(document.querySelectorAll('[data-page-row]'));
      const visibleCount = document.querySelector('#visible-page-count');
      if (search && visibleCount) {{
        search.addEventListener('input', () => {{
          const query = search.value.trim().toLowerCase();
          let count = 0;
          pageRows.forEach((row) => {{
            const visible = !query || row.dataset.search.includes(query);
            row.hidden = !visible;
            if (visible) count += 1;
          }});
          visibleCount.textContent = String(count);
        }});
      }}
    }})();
  </script>
</body>
</html>
"""
