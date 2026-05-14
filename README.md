# Korea Memory Pulse

3-hour automated brief on Samsung Electronics (005930.KS) and SK Hynix (000660.KS), with peer complex, DART filings, derivatives signals, and a Claude-synthesized analyst commentary. Static dashboard hosted on GitHub Pages, pipeline runs in GitHub Actions, costs ~$5–15/mo in Anthropic API.

```
┌─ GitHub Actions cron (every 3h)
│   └─ pipeline/run.py
│        ├─ sources/prices.py     (Yahoo + Alpha Vantage)
│        ├─ sources/dart.py       (Korean FSS disclosures)
│        ├─ sources/memory.py     (DRAM/NAND spot, manual or stub)
│        └─ synthesize.py         (Claude Sonnet 4 + web_search)
│
├─ commits docs/data/latest.json
│
└─ GitHub Pages serves docs/index.html
     └─ app.js fetches latest.json and renders
```

## Setup

### 1. Push this to a new GitHub repo

```bash
git init
git add .
git commit -m "init korea memory pulse"
git remote add origin git@github.com:<you>/<repo>.git
git push -u origin main
```

### 2. Enable GitHub Pages

Repo → Settings → Pages → Source: **Deploy from branch** → Branch: **main** → Folder: **/docs** → Save.

Your dashboard will be at `https://<you>.github.io/<repo>/`.

### 3. Add API key secrets

Repo → Settings → Secrets and variables → Actions → New repository secret. Add three:

| Name | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys. Required. |
| `ALPHA_VANTAGE_API_KEY` | alphavantage.co/support/#api-key (free tier 25 req/day; $50/mo entry for more). Optional - pipeline falls back to Yahoo if absent. |
| `DART_API_KEY` | opendart.fss.or.kr → Open API → Apply (free, instant). Optional but recommended for filings. |

### 4. Trigger the first run

Actions tab → `refresh-korea-semis` → **Run workflow**. Watch the logs. After completion you'll see a commit `refresh: <timestamp>` and the dashboard will populate.

After that, it runs automatically every 3 hours.

## Local development

```bash
cd pipeline
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export DART_API_KEY=...
export ALPHA_VANTAGE_API_KEY=...  # optional
python run.py
```

Then serve the dashboard locally:

```bash
cd docs
python -m http.server 8000
# open http://localhost:8000
```

## Customizing

- **Universe**: edit `pipeline/universe.py` to add/remove peers, indices, ADRs, or DART corp codes. Each ticker is one Yahoo call (batched, cheap) and one optional Alpha Vantage call (rate-limited).
- **Cadence**: edit cron in `.github/workflows/refresh.yml`. Current `0 */3 * * *` = every 3 hours UTC. Consider denser during KR session (00:00-06:30 UTC) and sparser overnight to save API tokens.
- **Brief schema**: edit the system prompt and schema instruction in `pipeline/synthesize.py`, then update `docs/app.js` to render any new fields.
- **Aesthetic**: all styling in `docs/styles.css`. CSS variables at the top control the full theme.
- **Memory pricing**: drop a `docs/data/memory_manual.json` with whatever structured DRAM/NAND/HBM spot levels you want to inject. The synthesizer will use it preferentially.

## Cost / scaling notes

- 8 runs/day × 30 days = 240 Claude API calls/month. At Sonnet 4 pricing with web_search and ~3k input + 1k output tokens per call, expect **$5–15/mo**.
- GitHub Actions: 240 runs × ~3 min = ~720 min/month. Free for public repos. Free tier is 2,000 min/month for private.
- Yahoo Finance unofficial API is rate-limited but our usage (one batched call per cycle) is well under any reasonable threshold. If it ever breaks, swap in `yfinance` or a paid alternative.

## Known gaps to wire later

- **DRAM/NAND contract pricing**: TrendForce gates this. Either pay them, scrape, or accept news-derived qualitative reads.
- **Intraday history charts**: snapshots accumulate in `docs/data/history/`. Wire Chart.js to render trailing-N-day trends if desired.
- **Alerting**: no push notifications today. Easiest add: SendGrid/Pushover call in `pipeline/run.py` when `brief.confidence == "high"` or a `material` filing fires.
- **Bloomberg/FactSet data**: can't be hit from a personal repo. Capital Group data stays at work.
