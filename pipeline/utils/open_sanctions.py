import pathway as pw
from functools import lru_cache

import requests, os
from dotenv import load_dotenv

load_dotenv()

def _os_one(
    qname: str,
    birth_date: str = None,
    nationality: str = None,
    alias: str = None,
):
    # it is tested that only these fields affect the matching results the most
    OS_API_KEY = os.environ["OS_API_KEY"]

    OS_URL = "https://api.opensanctions.org/match/default"
    _http = requests.Session()

    headers = {"Authorization": OS_API_KEY}

    props = {"name": [qname]}

    if birth_date:
        props["birthDate"] = [birth_date]
    if nationality:
        props["nationality"] = [nationality]
    if alias:
        props["alias"] = [alias]

    payload = {"queries": {"q": {"schema": "Person", "properties": props}}}

    r = _http.post(OS_URL, headers=headers, json=payload, timeout=30)
    r.raise_for_status()

    res = r.json().get("responses", {}).get("q", {}).get("results", []) or []
    if not res:
        return {"entity_id": None, "entity_name": None, "score": None, "data": None}

    m = res[0] # everything else is usually (almost always) score 0 since summation(all items['scores']) = 1
    ent = (m.get("entity") or {})
    props_res = (ent.get("properties") or {})
    names = props_res.get("name") or []

    return {
        "entity_id": ent.get("id"),
        "entity_name": names[0] if names else None,
        "score": m.get("score"),
        "data": m,
    }

@lru_cache(maxsize=5000)
def _os_lookup_cached(qname: str, birth_date: str = None, nationality: str = None, alias: str = None) -> dict:
    q = (qname or "").strip().lower()
    if not q:
        return {"entity_id": None, "entity_name": None, "score": None, "data": None}
    try:
        return _os_one(q, birth_date, nationality, alias)
    except Exception as e:
        return {"entity_id": None, "entity_name": None, "score": None, "data": {"error": str(e)}}

@pw.udf
def os_lookup(name: str | None, birth_date: str = None, nationality: str = None, alias: str = None) -> dict:
    return _os_lookup_cached(name or "", birth_date, nationality, alias)
