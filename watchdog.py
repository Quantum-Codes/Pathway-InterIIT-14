# watchdog.py
from __future__ import annotations

import os
from pyexpat import model
import re
import json
import time
import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple
from guardrails import Guard, OnFailAction
from guardrails.hub import CompetitorCheck, ToxicLanguage, ProfanityFree, GibberishText

import requests
import pathway as pw
from pathway.xpacks.llm import llms

# ---------- optional helpers you already have ----------
from compliance_data_reader import read_scraped_articles
from llm_output import generate_content, make_llm_prompt, parse_raw_llm_text, run_web_analysis
from sus import (
    check_alienvault,
    analyze_article_authenticity_with_metadata,
    check_domain_history,
)
from scraping_test_new import (
    fetch_articles_from_urls,
    run_scraper,
)
from open_sanctions import (
    _os_one,
    _os_lookup_cached,
    os_lookup,
)
from utils import compute_risk_from_score, extract_json_and_summary, parse_json_score, to_int_safe, to_lower

# =============================================================================
# Config & Logging
# =============================================================================
def _abs_glob(glob_str: str) -> str:
    p = Path(os.path.expanduser(glob_str))
    parent = p.parent.resolve()
    return str(parent / p.name)

INBOX_GLOB = _abs_glob(os.getenv("INBOX_GLOB", "inbox/entity_updates.csv"))
OUT_DIR = Path(os.getenv("OUT_DIR", "out")).resolve()
WATCHDOG_DIR = OUT_DIR / "watchdog"
WATCHDOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("pathway_watchdog")

OS_API_KEY="50fb68336ac9a4f12a79699431fb41df"           # required
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")   # optional
OTX_API_KEY = "8a525b4fff1ae49cc2c66151934b0c06bee3ce61670e1d20bd936a7f105190da"         # optional

model = llms.LiteLLMChat(
    model="mistral/mistral-small-latest", 
    api_key="CPiY2HbKGwO9Ht4uaBnIzJzOI1c5Ynhw", 
)

guard = Guard().use_many(
    ToxicLanguage(threshold=0.5, validation_method="sentence", on_fail=OnFailAction.EXCEPTION),
    ProfanityFree(on_fail=OnFailAction.EXCEPTION),
)

if not OS_API_KEY:
    raise RuntimeError("OS_API_KEY not set. `export OS_API_KEY=...`")

print(f"[watchdog] Reading from: {INBOX_GLOB}")
print(f"[watchdog] Writing to: {WATCHDOG_DIR}")


# =============================================================================
# Ingestion: SAME CSV INPUT as main.py, but in STATIC mode
# =============================================================================
class EntitiesSchema(pw.Schema):
    entity_id: str
    name: str
    age: str | None
    gender: str | None

# Read the SAME CSV files, but in STATIC mode (one-time read)
entities = pw.io.csv.read(
    path=INBOX_GLOB,
    schema=EntitiesSchema,
    mode="static",  # STATIC mode = read once and process
)

raw_ingest = entities.select(
    entity_id       =   pw.this.entity_id, 
    name            =   pw.this.name, 
    age             =   pw.this.age,
    gender          =   pw.this.gender,
)

pw.io.jsonlines.write(raw_ingest, str(WATCHDOG_DIR / "raw_ingest_initial.jsonl"))

# Add check timestamp to track when this re-evaluation happened
entities_with_timestamp = entities.select(
    entity_id           =   pw.this.entity_id,
    name                =   pw.this.name,
    age                 =   pw.this.age,
    gender              =   pw.this.gender,
    check_timestamp     =   time.time(),
)

# Diagnostics for what was read
raw_ingest = entities_with_timestamp.select(
    entity_id           =   pw.this.entity_id, 
    name                =   pw.this.name, 
    age                 =   pw.this.age, 
    gender              =   pw.this.gender,
    check_timestamp     =   pw.this.check_timestamp,
)

pw.io.jsonlines.write(raw_ingest, str(WATCHDOG_DIR / "raw_ingest.jsonl"))

canonical = entities_with_timestamp.select(
    entity_id        = pw.this.entity_id,
    raw_name         = pw.this.name,
    canonical_name   = to_lower(pw.this.name),
    canonical_age    = to_int_safe(pw.this.age),
    canonical_gender = to_lower(pw.this.gender),
    check_timestamp  = pw.this.check_timestamp,
)

# =============================================================================
# Enrichment: OS lookup, then web+LLM (SAME as main.py)
# =============================================================================
enriched = canonical.select(
    entity_id       = pw.this.entity_id,
    name            = pw.this.raw_name,
    canonical_name  = pw.this.canonical_name,
    check_timestamp = pw.this.check_timestamp,
    _os             = os_lookup(pw.this.canonical_name),   # dict -> pw.Json
).select(
    entity_id       = pw.this.entity_id,
    name            = pw.this.name,
    canonical_name  = pw.this.canonical_name,
    check_timestamp = pw.this.check_timestamp,
    os_entity_id    = pw.this._os["entity_id"],
    os_entity_name  = pw.this._os["entity_name"],
    os_score        = pw.this._os["score"],
    os_raw          = pw.this._os["data"],
)

# Append enriched matches
pw.io.jsonlines.write(enriched, str(WATCHDOG_DIR / "opensanctions_results.jsonl"))

with_web = enriched.select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    check_timestamp = pw.this.check_timestamp,
    web_tuple      = run_web_analysis(pw.this.canonical_name, filename="./agent_web_articles.jsonl"),
).select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    check_timestamp = pw.this.check_timestamp,
    web_prompt     = pw.this.web_tuple[0],
    citations      = pw.this.web_tuple[1],
)

pw.io.jsonlines.write(with_web, str(WATCHDOG_DIR / "web_analysis_debug.jsonl"))

llm_ready = with_web.select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    web_prompt     = pw.this.web_prompt,
    citations      = pw.this.citations,
    check_timestamp = pw.this.check_timestamp,
    system_prompt  = make_llm_prompt(pw.this.name, pw.this.os_entity_name, pw.this.os_score, pw.this.web_prompt)[0],
    user_prompt    = make_llm_prompt(pw.this.name, pw.this.os_entity_name, pw.this.os_score, pw.this.web_prompt)[1],
    fallback_json  = compute_risk_from_score(pw.this.os_score),
)

llm_called = llm_ready.select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    web_prompt     = pw.this.web_prompt,
    citations      = pw.this.citations,
    check_timestamp = pw.this.check_timestamp,
    fallback_json  = pw.this.fallback_json,
    llm_text       = generate_content(pw.this.system_prompt, pw.this.user_prompt), 
)

pw.io.jsonlines.write(llm_called, str(WATCHDOG_DIR / "llm_called_debug.jsonl"))

final_report = llm_called.select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    parsed         = parse_raw_llm_text(pw.this.llm_text),
    citations      = pw.this.citations,
    check_timestamp = pw.this.check_timestamp,
    ts             = time.time(),
).select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    risk_json      = pw.this.parsed[0],   # dict -> pw.Json
    summary        = pw.this.parsed[1],
    citations      = pw.this.citations,
    check_timestamp = pw.this.check_timestamp,
    timestamp      = pw.this.ts,
)

# Append-only outputs to watchdog directory
pw.io.jsonlines.write(final_report, str(WATCHDOG_DIR / "reports.jsonl"))
pw.io.jsonlines.write(
    llm_called.select(
        entity_id       =   pw.this.entity_id, 
        name            =   pw.this.name, 
        llm_text        =   pw.this.llm_text,
        check_timestamp =   pw.this.check_timestamp,
    ),
    str(WATCHDOG_DIR / "llm_debug.jsonl"),
)

# Latest snapshot for watchdog
latest = final_report.groupby(pw.this.entity_id).reduce(
    entity_id      = pw.this.entity_id,
    name           = pw.reducers.latest(pw.this.name),
    os_entity_name = pw.reducers.latest(pw.this.os_entity_name),
    os_score       = pw.reducers.latest(pw.this.os_score),
    risk_json      = pw.reducers.latest(pw.this.risk_json),
    summary        = pw.reducers.latest(pw.this.summary),
    citations      = pw.reducers.latest(pw.this.citations),
    check_timestamp = pw.reducers.max(pw.this.check_timestamp),
    timestamp      = pw.reducers.max(pw.this.timestamp),
)
pw.io.fs.write(latest, filename=str(WATCHDOG_DIR / "latest.jsonl"), format="json")

# =============================================================================
# Run (Static mode - processes once and exits)
# =============================================================================
if __name__ == "__main__":
    log.info("Starting Pathway watchdog run (static mode)...")
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)
    log.info("Watchdog check completed successfully")