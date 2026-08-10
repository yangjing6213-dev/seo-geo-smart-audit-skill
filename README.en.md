# SearchScope | Independent Site SEO/GEO Auditor

<p align="center">
  <img src="assets/logo-en.png" alt="Project logo" width="180">
</p>

SearchScope makes websites easier for search engines and AI systems to discover, understand, and cite.

[简体中文](README.md) | [English](README.en.md)

[![CI](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/actions/workflows/ci.yml) [![CodeQL](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/actions/workflows/codeql.yml/badge.svg)](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/actions/workflows/codeql.yml)

![Project workflow cover](assets/project-cover-en.png)

SearchScope is a read-only SEO/GEO auditing Skill for public independent websites. It checks crawl and index signals, metadata, canonical URLs, hreflang, structured data, AI crawler access, and citation readiness, then produces prioritized fixes with evidence and verification steps.

- Product: SearchScope
- Skill identifier: `independent-site-seo-geo-auditor`
- Skill version: `1.4.1`
- Rule engine: `1.4.9`
- Creator: [ENHE AI Studio](https://www.enhe-tech.com.cn)

## Capabilities

- Inspect `robots.txt`, sitemaps, HTTP status, noindex directives, and redirects.
- Normalize pages by final URL and canonical before duplicate metadata or hreflang grouping.
- Check titles, descriptions, headings, image alt text, and internal links.
- Separate verified evidence from render-required and external-data-required checks.
- Assess AI crawler access, entity signals, machine-readable resources, and citation readiness.
- Generate JSON, Markdown, and self-contained HTML reports.
- Run a bilingual local web interface for read-only audits of public URLs.

## Requirements

- Python 3.10 or later.
- Runtime code uses only the Python standard library.
- Node.js is optional and used only for JavaScript syntax validation.

## Install as a Codex Skill

```bash
git clone https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill.git ~/.codex/skills/independent-site-seo-geo-auditor
```

Restart Codex or reload Skills, then invoke `independent-site-seo-geo-auditor`.

## Command-line audit

```bash
python scripts/site_audit.py https://example.com \
  --max-pages 25 \
  --json-out audit.json \
  --markdown-out audit.md \
  --html-out audit.html
```

Private, loopback, reserved, and credential-bearing URLs are rejected by default. Crawling remains on the target origin.

## Web interface

```bash
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Set the `PORT` environment variable to use another port.

The public read-only audit endpoint is `POST /api/audit`. Send `{"url":"https://example.com","max_pages":25}` and request no more than 300 same-origin pages. `GET /api/health` reports the read-only mode and audit capability status.

## Validation

```bash
python -m unittest discover -s tests -v
python scripts/test_site_audit.py
python -m compileall -q app.py scripts tests
node --check web/app.js
```

## Repository layout

```text
SKILL.md                 Codex/Agent Skill entry point
agents/                  Agent display metadata
scripts/                 Audit engine, HTML renderer, and engine tests
references/              Scoring and evidence rules
assets/                  Markdown report template
app.py                   Local read-only web server
web/                     Bilingual user interface
tests/                   Web entry-point tests
```

## Safety and result boundaries

SearchScope does not sign in to target sites, submit forms, or modify production data. It does not treat response time as Core Web Vitals and does not guarantee indexing, ranking, or AI citations. Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing. See [SUPPORT.md](SUPPORT.md) for supported requests and boundaries.

## License

Licensed under the [Apache License 2.0](LICENSE).
