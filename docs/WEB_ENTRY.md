# Web Entry Points

SearchScope supports a local self-install path and a separately deployed online path.

## Option 1: Self-install

Clone the repository and start the local web app:

```bash
git clone https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill.git
cd seo-geo-smart-audit-skill
python app.py
```

Open `http://127.0.0.1:8000` on the same computer. `127.0.0.1` is a loopback address: another user's computer cannot use that address to reach your local process.

The app binds only to `127.0.0.1`. Web audits have a 180-second total limit. `GET /api/audit/status` exposes page-count progress, and the interface can cancel the active audit. Cancellation and timeout return an error instead of a partial-success report.

You can optionally select a UTF-8 JSON file containing Search Console metrics or answer-engine citation samples. The app validates and summarizes it in memory; raw rows, query text, and credentials are not stored. See [external evidence format](external-evidence.md).

The audit form also offers optional browser rendering for JavaScript-loaded page metadata. It is off by default and needs a separate Playwright and Chromium setup. See [browser rendering setup and limits](browser-rendering.md). The web option is unavailable until both are installed.

The local app uses only the Python standard library. Set `PORT` before starting the app when port 8000 is unavailable:

```bash
PORT=8001 python app.py
```

On Windows PowerShell:

```powershell
$env:PORT = "8001"
python app.py
```

## Option 2: Online access

Open the separately deployed online entry point:

<https://enheai-seo-geo.coze.site/>

The repository records this URL as a user-facing entry point; its deployment, availability, and service limits are outside this source repository. The URL returned HTTP 200 during the documentation update check on 2026-08-10.

## Safety boundary

The audit is read-only and accepts public HTTP(S) targets. Do not expose a local development port directly to the public Internet without a properly configured HTTPS reverse proxy, process supervision, rate limiting, and monitoring.
