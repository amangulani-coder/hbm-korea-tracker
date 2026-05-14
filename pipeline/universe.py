"""
Reference data for tickers, peers, and Korean corp codes.

Edit this file to expand coverage. Keep it lean: every ticker added means
another Alpha Vantage call per run (5 calls/min on free tier).
"""

# Primary names
PRIMARY = {
    "005930.KS": {"name": "Samsung Electronics", "type": "memory_logic"},
    "000660.KS": {"name": "SK Hynix",           "type": "memory_pure"},
}

# Peer set - memory, WFE, foundry. Tune to taste.
PEERS = {
    # Memory
    "MU":       {"name": "Micron",          "group": "memory"},
    "WDC":      {"name": "Western Digital", "group": "memory"},
    "285A.T":   {"name": "Kioxia",          "group": "memory"},
    # WFE
    "ASML":     {"name": "ASML",            "group": "wfe"},
    "AMAT":     {"name": "Applied Materials","group": "wfe"},
    "LRCX":     {"name": "Lam Research",    "group": "wfe"},
    "KLAC":     {"name": "KLA",             "group": "wfe"},
    "8035.T":   {"name": "Tokyo Electron",  "group": "wfe"},
    # Foundry / logic
    "TSM":      {"name": "TSMC",            "group": "foundry"},
    "NVDA":     {"name": "Nvidia",          "group": "compute"},
}

# Korean indices and FX
MACRO = {
    "^KS11":    "KOSPI Composite",
    "USDKRW=X": "USD/KRW",
    "KS200=F":  "KOSPI 200 futures",
}

# ADR proxies for after-hours sanity
ADRS = {
    "SSNLF": "Samsung ADR (OTC)",
    "HXSCL": "SK Hynix ADR (OTC)",
}

# DART corp codes (8 digits). Lookup at opendart.fss.or.kr if expanding.
# These are stable - Samsung and SK Hynix corp codes don't change.
DART_CORPS = {
    "Samsung Electronics": "00126380",
    "SK Hynix":            "00164779",
}
