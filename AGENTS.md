# SearchScope repository instructions

## Project overview

SearchScope is a read-only SEO/GEO audit Skill and local web application for public independent websites. The stable Skill identifier is `independent-site-seo-geo-auditor`.

## Repository structure

- `SKILL.md`, `agents/`, `references/`, and `assets/` define the Skill contract.
- `scripts/` owns crawling, evidence classification, scoring, reporting, and engine tests.
- `app.py` and `web/` own the local bilingual web entry point.
- `tests/` owns web application tests.

## Development commands

```bash
python app.py
python scripts/site_audit.py https://example.com --max-pages 25
```

## Required checks

```bash
python -m unittest discover -s tests -v
python scripts/test_site_audit.py
python -m compileall -q app.py scripts tests
node --check web/app.js
```

## Dependency rules

Runtime code uses the Python standard library. Discuss and document any new runtime dependency before adding it. Do not add a package manager or framework without a demonstrated need.

## Safety and secret rules

- Keep the audit read-only and limited to public HTTP(S) URLs.
- Preserve private, loopback, reserved-address, and credential-bearing URL blocks.
- Never commit credentials, cookies, private reports, browser profiles, customer data, or real `.env` values.
- Do not log complete user-supplied target URLs or report contents.

## Documentation and Git rules

- Keep `README.md` and `README.en.md` synchronized.
- Add focused tests for behavior and rule changes.
- Preserve unrelated user changes and avoid destructive Git commands.
- Stage explicit intended paths; do not use `git add .` or `git add -A` for releases.
- Never force-push, bypass push protection, publish a release, or modify remote settings without explicit approval and a passing local pre-publish report.

## Definition of done

The intended tests and syntax checks pass, security boundaries remain intact, documentation reflects verified behavior, and no generated reports or secrets are staged.
