"""
DART (Data Analysis, Retrieval and Transfer System) - Korea FSS.

Get a free API key at: https://opendart.fss.or.kr -> Open API -> Apply
Endpoint docs (Korean): https://opendart.fss.or.kr/guide/main.do

We pull the disclosure list for the last 24 hours for each tracked corp.
The 'report_nm' field is Korean - Claude translates during synthesis.
"""

from __future__ import annotations
import os
import requests
from datetime import datetime, timedelta, timezone

DART_KEY = os.environ.get("DART_API_KEY", "")
LIST_URL = "https://opendart.fss.or.kr/api/list.json"


def fetch_filings(corp_codes: dict[str, str], hours_back: int = 24) -> list[dict]:
    """
    Returns list of recent filings across all corp_codes.

    corp_codes: {"Samsung Electronics": "00126380", "SK Hynix": "00164779"}
    """
    if not DART_KEY:
        print("[dart] no API key set, skipping")
        return []

    end = datetime.now(timezone.utc)
    bgn = end - timedelta(hours=hours_back)
    bgn_de = bgn.strftime("%Y%m%d")
    end_de = end.strftime("%Y%m%d")

    out: list[dict] = []
    for name, code in corp_codes.items():
        try:
            r = requests.get(
                LIST_URL,
                params={
                    "crtfc_key": DART_KEY,
                    "corp_code": code,
                    "bgn_de": bgn_de,
                    "end_de": end_de,
                    "page_count": 50,
                },
                timeout=15,
            )
            r.raise_for_status()
            payload = r.json()
            if payload.get("status") not in ("000", "013"):
                print(f"[dart] {name}: status={payload.get('status')} msg={payload.get('message')}")
                continue
            for f in payload.get("list", []) or []:
                out.append({
                    "company": name,
                    "corp_code": code,
                    "report_nm_kr": f.get("report_nm"),  # Korean - Claude translates
                    "rcept_no": f.get("rcept_no"),
                    "rcept_dt": f.get("rcept_dt"),
                    "flr_nm": f.get("flr_nm"),
                    "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={f.get('rcept_no')}",
                })
        except Exception as e:
            print(f"[dart] {name}: {e}")
    return out
