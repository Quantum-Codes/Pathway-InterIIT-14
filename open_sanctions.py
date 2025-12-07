import pathway as pw
from functools import lru_cache

import requests       # required

def _os_one(qname: str) -> dict:
    OS_API_KEY="50fb68336ac9a4f12a79699431fb41df"    

    OS_URL = "https://api.opensanctions.org/match/default"
    _http = requests.Session()

    headers = {"Authorization": OS_API_KEY}
    payload = {"queries": {"q": {"schema": "Person", "properties": {"name": [qname]}}}}
    r = _http.post(OS_URL, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    res = r.json().get("responses", {}).get("q", {}).get("results", []) or []
    if not res:
        return {"entity_id": None, "entity_name": None, "score": None, "data": None}
    m = res[0]
    ent = (m.get("entity") or {})
    props = (ent.get("properties") or {})
    names = props.get("name") or []
    return {
        "entity_id": ent.get("id"),
        "entity_name": names[0] if names else None,
        "score": m.get("score"),
        "data": m,
    }

@lru_cache(maxsize=5000)
def _os_lookup_cached(qname: str) -> dict:
    q = (qname or "").strip().lower()
    if not q:
        return {"entity_id": None, "entity_name": None, "score": None, "data": None}
    try:
        return _os_one(q)
    except Exception as e:
        return {"entity_id": None, "entity_name": None, "score": None, "data": {"error": str(e)}}

@pw.udf
def os_lookup(name: str | None) -> dict:
    return _os_lookup_cached(name or "")