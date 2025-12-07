# main.py
from __future__ import annotations

import os
from pyexpat import model
import re
import json
import shutil
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

# kafka topics
DB_TOPIC = 'db_updates'
MAIN_BACKEND_TOPIC = 'entities'

INBOX_GLOB = _abs_glob(os.getenv("INBOX_GLOB", "inbox/entity_updates.csv"))
OUT_DIR = Path(os.getenv("OUT_DIR", "out")).resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("pathway_pipeline")

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
    # GibberishText(threshold=0.5, validation_method="sentence", on_fail=OnFailAction.EXCEPTION)
    # ShieldGemma2B(score_threshold=0.5, on_fail=OnFailAction.EXCEPTION),
    # LlamaGuard7B(policies=[LlamaGuard7B.POLICY__NO_ILLEGAL_DRUGS], on_fail=OnFailAction.EXCEPTION)
)

if not OS_API_KEY:
    raise RuntimeError("OS_API_KEY not set. `export OS_API_KEY=...`")

print(f"[streaming] Watching: {INBOX_GLOB}")
print(f"[streaming] Writing to: {OUT_DIR}")

# =============================================================================
# OpenSanctions: per-row lookup (cached)
# =============================================================================
# Example usage:
# example_string = "..."  # put your full input string here
# js, summary = extract_json_and_summary(example_string)
# print(js)       # Python dict (or error dict if parsing failed)
# print(summary)  # string

# =============================================================================
# Ingestion: STREAMING CSVs
# =============================================================================
class EntitiesSchema(pw.Schema):
    # IMPORTANT: no primary_key in streaming
    entity_id: str
    name: str
    age: str | None
    gender: str | None

rdkafka_settings = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "0",
    "session.timeout.ms": "6000",
    "auto.offset.reset": "earliest",
}

# entities = pw.io.kafka.read(
#     rdkafka_settings,
#     topic=MAIN_BACKEND_TOPIC,
#     format="json",
#     schema=EntitiesSchema,
#     autocommit_duration_ms=100,
# )

entities = pw.io.csv.read(
    path=INBOX_GLOB,
    schema=EntitiesSchema,
    mode="streaming",
)

# Diagnostics for what was read
raw_ingest = entities.select(
    entity_id=pw.this.entity_id, name=pw.this.name, age=pw.this.age, gender=pw.this.gender
)
pw.io.jsonlines.write(raw_ingest, str(OUT_DIR / "raw_ingest.jsonl"))

canonical = entities.select(
    entity_id        = pw.this.entity_id,
    raw_name         = pw.this.name,
    canonical_name   = to_lower(pw.this.name),
    canonical_age    = to_int_safe(pw.this.age),
    canonical_gender = to_lower(pw.this.gender),
)

# =============================================================================
# Enrichment: OS lookup, then web+LLM (optional)
# =============================================================================
enriched = canonical.select(
    entity_id       = pw.this.entity_id,
    name            = pw.this.raw_name,
    canonical_name  = pw.this.canonical_name,
    _os             = os_lookup(pw.this.canonical_name),   # dict -> pw.Json
).select(
    entity_id       = pw.this.entity_id,
    name            = pw.this.name,
    canonical_name  = pw.this.canonical_name,
    os_entity_id    = pw.this._os["entity_id"],
    os_entity_name  = pw.this._os["entity_name"],
    os_score        = pw.this._os["score"],
    os_raw          = pw.this._os["data"],
)

# Append enriched matches
pw.io.jsonlines.write(enriched, str(OUT_DIR / "opensanctions_results.jsonl"))

with_web = enriched.select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    web_tuple      = run_web_analysis(pw.this.canonical_name),
).select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    web_prompt     = pw.this.web_tuple[0],
    citations      = pw.this.web_tuple[1],
)

pw.io.jsonlines.write(with_web, str(OUT_DIR / "web_analysis_debug.jsonl"))

llm_ready = with_web.select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    web_prompt     = pw.this.web_prompt,
    citations      = pw.this.citations,
    system_prompt  = make_llm_prompt(pw.this.name, pw.this.os_entity_name, pw.this.os_score, pw.this.web_prompt)[0],
    user_prompt    = make_llm_prompt(pw.this.name, pw.this.os_entity_name, pw.this.os_score, pw.this.web_prompt)[1],
    fallback_json  = compute_risk_from_score(pw.this.os_score),
)

# pw.io.jsonlines.write(llm_ready, str(OUT_DIR / "llm_ready_debug.jsonl"))

llm_called = llm_ready.select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    web_prompt     = pw.this.web_prompt,
    citations      = pw.this.citations,
    fallback_json  = pw.this.fallback_json,
    # llm_text       = call_gemini_if_configured(pw.this.prompt),
    llm_text       = generate_content(pw.this.system_prompt, pw.this.user_prompt), 
)

pw.io.jsonlines.write(llm_called, str(OUT_DIR / "llm_called_debug.jsonl"))

final_report = llm_called.select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    # parsed         = parse_llm_text_or_fallback(pw.this.llm_text, pw.this.fallback_json),
    parsed         = parse_raw_llm_text(pw.this.llm_text),
    citations      = pw.this.citations,
    ts             = time.time(),
).select(
    entity_id      = pw.this.entity_id,
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    risk_json      = pw.this.parsed[0],   # dict -> pw.Json
    summary        = pw.this.parsed[1],
    citations      = pw.this.citations,
    timestamp      = pw.this.ts,
)

# Append-only outputs
pw.io.jsonlines.write(final_report, str(OUT_DIR / "reports.jsonl"))
pw.io.jsonlines.write(
    llm_called.select(entity_id=pw.this.entity_id, name=pw.this.name, llm_text=pw.this.llm_text),
    str(OUT_DIR / "llm_debug.jsonl"),
)

# Optional: latest-per-entity snapshot (compatible with your Pathway version)
latest = final_report.groupby(pw.this.entity_id).reduce(
    entity_id      = pw.this.entity_id,
    name           = pw.reducers.latest(pw.this.name),
    os_entity_name = pw.reducers.latest(pw.this.os_entity_name),
    os_score       = pw.reducers.latest(pw.this.os_score),
    risk_json      = pw.reducers.latest(pw.this.risk_json),
    summary        = pw.reducers.latest(pw.this.summary),
    citations      = pw.reducers.latest(pw.this.citations),
    timestamp      = pw.reducers.max(pw.this.timestamp),
)
pw.io.fs.write(latest, filename=str(OUT_DIR / "latest.jsonl"), format="json")

pw.io.kafka.write(
    final_report,
    rdkafka_settings,
    topic_name=DB_TOPIC,
    format="json",
)

# =============================================================================
# Run (Pathway versions without MonitoringMode/autocommit use bare run())
# =============================================================================

def clean_persistent_storage():
    if os.path.exists("./PState"):
        shutil.rmtree("./PState")

if __name__ == "__main__":
    log.info("Starting Pathway streaming run...")

    # clears the storage file created
    # clean_persistent_storage()

    # Change: persistence config created
    backend = pw.persistence.Backend.filesystem("./PState")
    persistence_config = pw.persistence.Config(backend)
    
    pw.run(
        monitoring_level=pw.MonitoringLevel.NONE, # no MonitoringMode / autocommit args in your version
        persistence_config=persistence_config, # Change: persistence config passed to the method
    )