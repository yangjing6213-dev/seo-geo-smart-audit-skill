# Repository Standard

This repository follows ENHE GitHub Open Source Standard v1.2.

## Identity and scope

- Product name: SearchScope
- Repository: `yangjing6213-dev/seo-geo-smart-audit-skill`
- Skill identifier: `independent-site-seo-geo-auditor`
- Skill version: `1.4.1`
- Rule engine: `1.4.9`
- License: Apache-2.0

The public scope contains the Skill, deterministic audit engine, self-contained report renderer, local read-only web interface, tests, and project governance. ENHE production workers, payment integrations, private reports, commercial plans, server details, and deployment credentials are excluded.

## Runtime and package management

Python 3.10 or later is required. Runtime code uses only the Python standard library. `package.json` provides convenience commands and metadata but declares no npm dependencies; no lockfile is required while dependency sets remain empty.

## Canonical checks

```bash
python -m unittest discover -s tests -v
python scripts/test_site_audit.py
python -m compileall -q app.py scripts tests
node --check web/app.js
```

GitHub Actions must run the same checks without deployment credentials. CI workflows use least-privilege permissions.

## Branching, versions, and releases

- The default branch is `main`.
- Feature work uses focused branches and pull requests.
- Skill and rule-engine versions are maintained independently and documented together.
- Tags and GitHub Releases require separate approval; a source push is not a marketplace publication.

## Security and disclosure

Use GitHub private security advisories for vulnerabilities. Do not place secret values, private target URLs, customer reports, browser profiles, or production data in issues, logs, fixtures, or commits.

## Licensing and provenance

Project code is licensed under Apache-2.0. Contributions and included assets must have traceable redistribution rights. External standards and documentation links are references, not vendored code.

## Release gates

Before any public write, generate a local Git-ignored pre-publish report, scan the worktree and history for secrets, inspect large files and third-party assets, run all canonical checks, verify the target owner and repository, and require `READY_TO_PUBLISH=YES`. Force pushes and bypasses are prohibited.
