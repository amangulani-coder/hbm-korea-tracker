"""
Memory spot pricing.

This is the hardest layer to source for free.

Known options:
  1. TrendForce DRAMeXchange spot pages - paywalled for contract, partial
     spot data scrapable but rate-limited and TOS-grey.
  2. DXI (DRAM Exchange Index) - published weekly by InSpectrum, free
     historical, light current.
  3. News-derived pricing - Reuters, Nikkei often cite spot levels in
     articles. Captured automatically by the news layer.
  4. Capital Group internal data (Bloomberg DRMD <Index>, etc.) - not
     hookable from a personal repo.

Default behavior here: stub returns placeholder structure. The synthesize
step will rely on news-derived pricing instead until you wire a real source.

When you want real spot data, options to plug in:
  - Scrape from TrendForce (be respectful of robots.txt)
  - Use a paid feed like Wright's, Witsview, or DRAMeXchange API ($)
  - Manually drop a CSV into docs/data/memory_manual.csv that you update weekly
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timezone


MANUAL_PATH = "docs/data/memory_manual.json"


def fetch_memory_pricing() -> dict:
    # If manual file exists, prefer it.
    if os.path.exists(MANUAL_PATH):
        try:
            with open(MANUAL_PATH) as f:
                manual = json.load(f)
            manual["source"] = "manual"
            return manual
        except Exception as e:
            print(f"[memory] manual file unreadable: {e}")

    # Stub - synthesize step will note this is news-derived only.
    return {
        "source": "stub",
        "as_of": datetime.now(timezone.utc).isoformat(),
        "note": (
            "No structured memory spot feed wired. Pricing context will be "
            "extracted from news flow by the synthesizer. Drop a JSON file at "
            f"{MANUAL_PATH} to override (keys: ddr5_8gb, ddr4_8gb, nand_512gb, "
            "hbm3e_premium, dxi_index, with values + as_of)."
        ),
        "metrics": {},
    }
