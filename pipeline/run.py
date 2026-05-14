"""
Pipeline orchestrator. Runs all source modules, hands raw data to the
synthesizer, writes latest.json + a timestamped historical snapshot.

Outputs:
  docs/data/latest.json
  docs/data/history/YYYY-MM-DDTHH-MM-SSZ.json
"""

from __future__ import annotations
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make pipeline/ importable
sys.path.insert(0, str(Path(__file__).parent))

import universe
from sources import prices, dart, memory
from synthesize import synthesize_brief


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "docs" / "data"
HISTORY_DIR = DATA_DIR / "history"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = utcnow_iso()
    print(f"[run] starting {timestamp}")

    # 1. Prices
    print("[run] fetching prices...")
    quotes = prices.fetch_all(
        primary=universe.PRIMARY,
        peers=universe.PEERS,
        macro=universe.MACRO,
        adrs=universe.ADRS,
    )

    # 2. DART filings
    print("[run] fetching DART filings...")
    filings = dart.fetch_filings(universe.DART_CORPS, hours_back=24)
    print(f"[run] {len(filings)} filings in last 24h")

    # 3. Memory pricing
    print("[run] fetching memory pricing...")
    memory_data = memory.fetch_memory_pricing()

    # 4. Synthesize - this calls Claude with web search for news flow
    print("[run] synthesizing brief via Claude...")
    raw_payload = {
        "as_of": timestamp,
        "quotes": quotes,
        "filings": filings,
        "memory": memory_data,
    }
    try:
        brief = synthesize_brief(raw_payload)
    except Exception as e:
        print(f"[run] synthesis failed: {e}")
        brief = {
            "error": str(e),
            "headline": "Synthesis unavailable",
            "summary": "Raw data still available below.",
        }

    output = {
        "generated_at": timestamp,
        "brief": brief,
        "data": raw_payload,
    }

    # Write latest
    latest_path = DATA_DIR / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"[run] wrote {latest_path}")

    # Write history snapshot
    hist_path = HISTORY_DIR / f"{timestamp.replace(':', '-')}.json"
    with open(hist_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"[run] wrote {hist_path}")

    # Prune history beyond 30 days to keep repo light
    cutoff_days = 30
    now = datetime.now(timezone.utc)
    for p in HISTORY_DIR.glob("*.json"):
        try:
            stem = p.stem.replace("-", ":", 2).replace("-", ":", 1)  # safe roundtrip
            # Just use file mtime to be simple and robust
            age_days = (now.timestamp() - p.stat().st_mtime) / 86400
            if age_days > cutoff_days:
                p.unlink()
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
