"""
Price source: Alpha Vantage for KR/US, Yahoo for indices/FX/futures.

Alpha Vantage free tier: 25 requests/day. Premium: 75/min @ $50/mo.
For 8 runs/day x ~13 tickers = 104 reqs/day, you need at least the entry
paid tier ($50/mo) or to fall back to Yahoo for everything.

Yahoo Finance has no official free API but yfinance / direct query.finance.yahoo.com
works for personal use. We use direct calls to avoid adding the yfinance dep.
"""

from __future__ import annotations
import os
import time
import requests
from typing import Iterable

ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
YAHOO_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
YAHOO_HEADERS = {"User-Agent": "Mozilla/5.0 (korea-semis-tracker)"}


def fetch_quote_alpha_vantage(symbol: str) -> dict | None:
    """GLOBAL_QUOTE endpoint - one ticker per call."""
    if not ALPHA_VANTAGE_KEY:
        return None
    try:
        r = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": ALPHA_VANTAGE_KEY,
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json().get("Global Quote", {})
        if not data or not data.get("05. price"):
            return None
        return {
            "symbol": symbol,
            "price": float(data["05. price"]),
            "change": float(data.get("09. change", 0) or 0),
            "change_pct": float((data.get("10. change percent", "0%") or "0%").rstrip("%")),
            "volume": int(float(data.get("06. volume", 0) or 0)),
            "prev_close": float(data.get("08. previous close", 0) or 0),
            "source": "alpha_vantage",
        }
    except Exception as e:
        print(f"[av] {symbol}: {e}")
        return None


def fetch_quotes_yahoo(symbols: Iterable[str]) -> dict[str, dict]:
    """Batch Yahoo lookup - up to ~50 symbols per call."""
    out: dict[str, dict] = {}
    syms = ",".join(symbols)
    if not syms:
        return out
    try:
        r = requests.get(
            YAHOO_QUOTE_URL,
            params={"symbols": syms},
            headers=YAHOO_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        for q in r.json().get("quoteResponse", {}).get("result", []) or []:
            sym = q.get("symbol")
            if not sym:
                continue
            out[sym] = {
                "symbol": sym,
                "price": q.get("regularMarketPrice"),
                "change": q.get("regularMarketChange"),
                "change_pct": q.get("regularMarketChangePercent"),
                "volume": q.get("regularMarketVolume"),
                "prev_close": q.get("regularMarketPreviousClose"),
                "market_state": q.get("marketState"),
                "currency": q.get("currency"),
                "source": "yahoo",
            }
    except Exception as e:
        print(f"[yahoo] batch failed: {e}")
    return out


def fetch_all(primary: dict, peers: dict, macro: dict, adrs: dict) -> dict:
    """
    Strategy: Yahoo for everything (free, batchable). Alpha Vantage as
    enrichment for primary names if you want a second source.
    Swap to AV-first if you have a premium key.
    """
    all_syms = list(primary) + list(peers) + list(macro) + list(adrs)
    yahoo = fetch_quotes_yahoo(all_syms)

    # Optional: cross-check primary names with Alpha Vantage if key is present.
    av: dict[str, dict] = {}
    if ALPHA_VANTAGE_KEY:
        for sym in primary:
            q = fetch_quote_alpha_vantage(sym)
            if q:
                av[sym] = q
            time.sleep(13)  # respect free-tier rate limits

    def merge(sym: str) -> dict:
        base = yahoo.get(sym, {"symbol": sym, "price": None})
        if sym in av:
            base["av_price"] = av[sym].get("price")
        return base

    return {
        "primary": {s: {**merge(s), **meta} for s, meta in primary.items()},
        "peers":   {s: {**merge(s), **meta} for s, meta in peers.items()},
        "macro":   {s: {**merge(s), "label": label} for s, label in macro.items()},
        "adrs":    {s: {**merge(s), "label": label} for s, label in adrs.items()},
    }
