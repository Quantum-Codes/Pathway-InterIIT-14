# sus.py
from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from OTXv2 import OTXv2, IndicatorTypes

def check_alienvault(url: str, api_key: str):
    """Check URL reputation/details on AlienVault OTX."""
    otx = OTXv2(api_key)
    indicators = otx.get_indicator_details_full(IndicatorTypes.URL, url)
    return indicators

def analyze_article_authenticity_with_metadata(url: str):
    """
    Inspect page metadata and structure for authenticity signals.
    Returns {"score": float 0..1, "signals": {...}}
    """
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")

    signals = {
        "has_author": bool(soup.find("meta", property="article:author")),
        "has_date": bool(soup.find("meta", property="article:published_time")),
        "has_links": len(soup.find_all("a", href=True)) > 5,
        "has_schema": bool(soup.find("script", type="application/ld+json")),
        "uses_https": url.startswith("https://"),
    }
    authenticity_score = sum(1 for v in signals.values() if v) / max(1, len(signals))
    return {"score": authenticity_score, "signals": signals}

def check_domain_history(url: str):
    """
    Query Wayback Machine for domain presence.
    """
    wayback_url = f"http://archive.org/wayback/available?url={url}"
    r = requests.get(wayback_url, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("archived_snapshots") and data["archived_snapshots"].get("closest"):
        first_snapshot = data["archived_snapshots"]["closest"].get("timestamp")
        return {"has_history": True, "first_archived": first_snapshot}
    return {"has_history": False}

def summarize_otx(indicators: dict) -> dict:
    """
    Compact summary from OTX indicator details: pulses count + tags.
    """
    info = (indicators or {}).get("pulse_info", {}) or {}
    pulses = info.get("pulses", []) or []
    tags = []
    for p in pulses:
        for t in p.get("tags", []) or []:
            if t not in tags:
                tags.append(t)
    return {
        "pulses_count": len(pulses),
        "tags": tags[:10],
    }
