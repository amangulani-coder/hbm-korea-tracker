"""
Synthesizer: feeds raw market data to Claude Sonnet 4 with web search enabled,
asks for a structured JSON brief.

Output schema (what the dashboard expects):
  {
    "headline": str,                       # one-line takeaway
    "summary": str,                        # 3-5 sentence prose
    "pair_trade_view": str,                # 005930 vs 000660 relative read
    "memory_cycle": {
      "stage": str,                        # "up", "late_up", "peak", "down", etc.
      "notes": str,
    },
    "hbm_pulse": str,                      # HBM3e / HBM4 / GB300 demand notes
    "key_filings": [                       # translated DART items
      {"company": str, "summary_en": str, "url": str, "material": bool}
    ],
    "news_pulse": [
      {"headline": str, "source": str, "url": str, "implication": str}
    ],
    "derivatives_signal": str,             # KOSPI200 fut, USD/KRW read
    "watch_for_next_3h": [str, ...],       # 2-5 catalysts
    "confidence": str,                     # "low"|"medium"|"high"
  }
"""

from __future__ import annotations
import json
import os
import re
import anthropic


MODEL = "claude-sonnet-4-5"  # bump as newer Sonnets ship

SYSTEM_PROMPT = """You are a sell-side semis analyst writing a 3-hour pulse \
for a buy-side associate covering Samsung Electronics (005930.KS) and SK Hynix \
(000660.KS). Voice: concise, direct, no hedging filler. Audience knows the \
sector. Translate any Korean filing titles to English. Cite specific data \
points from the payload. Use web_search to pull last-12-hours news flow on \
HBM, DRAM/NAND pricing, hyperscaler capex commentary, and CoWoS supply. \
Always return ONLY valid JSON matching the schema specified - no markdown, \
no prose preamble, no trailing commentary."""


SCHEMA_INSTRUCTION = """Return a single JSON object with keys: headline (str), \
summary (str, 3-5 sentences), pair_trade_view (str, Samsung vs SK Hynix \
relative read), memory_cycle (object with stage and notes), hbm_pulse (str), \
key_filings (array of {company, summary_en, url, material:bool}), \
news_pulse (array of {headline, source, url, implication}, max 8 items), \
derivatives_signal (str), watch_for_next_3h (array of strings, 2-5 items), \
confidence (str: low|medium|high)."""


def _extract_json(text: str) -> dict:
    """Tolerate code fences if the model adds them despite instructions."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


def synthesize_brief(payload: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    user_msg = (
        f"Raw market payload (as of {payload.get('as_of')}):\n\n"
        f"```json\n{json.dumps(payload, ensure_ascii=False)[:18000]}\n```\n\n"
        f"{SCHEMA_INSTRUCTION}"
    )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}],
        messages=[{"role": "user", "content": user_msg}],
    )

    # Concatenate all text blocks (web_search results interleave)
    text_chunks = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    raw = "\n".join(text_chunks).strip()

    try:
        return _extract_json(raw)
    except Exception:
        # Last-ditch: try to find a {...} block
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return _extract_json(m.group(0))
        raise
