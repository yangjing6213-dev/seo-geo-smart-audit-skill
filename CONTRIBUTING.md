# Contributing

Thank you for contributing to SearchScope.

## Before opening a change

1. Search existing issues and pull requests.
2. Open an issue for behavior changes that affect audit rules, scoring, or safety boundaries.
3. Do not include credentials, private URLs, customer reports, browser profiles, or production data.

## Development

Use Python 3.10 or later. Runtime code must remain compatible with the Python standard library unless a dependency change is discussed and approved first.

```bash
python -m unittest discover -s tests -v
python scripts/test_site_audit.py
python -m compileall -q app.py scripts tests
node --check web/app.js
```

## Pull requests

- Keep changes focused and document user-visible behavior.
- Add or update tests for audit-rule and safety changes.
- Preserve the read-only and public-URL-only boundaries.
- Update both Chinese and English documentation when facts or commands change.
- Confirm that new code and assets can be redistributed under Apache-2.0 and include required attribution.

By contributing, you agree that your contribution is licensed under Apache License 2.0.

Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report vulnerabilities privately through the process in [SECURITY.md](SECURITY.md).
