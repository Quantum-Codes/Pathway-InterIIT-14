# watchdog.py
from __future__ import annotations

import os, sys
import time
import logging
from pathlib import Path
from guardrails import Guard, OnFailAction
from guardrails.hub import ToxicLanguage, ProfanityFree
import pathway as pw
from dotenv import load_dotenv

# ---------- optional helpers you already have ----------
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.llm_output import run_web_analysis
from utils.open_sanctions import (
    os_lookup,
)

# =============================================================================
# Config & Logging
# =============================================================================
def _abs_glob(glob_str: str) -> str:
    p = Path(os.path.expanduser(glob_str))
    parent = p.parent.resolve()
    return str(parent / p.name)

load_dotenv()

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

OS_API_KEY=os.environ["OS_API_KEY"]           # required
GEMINI_API_KEY = os.environ.get("GOOGLE_CLOUD_API_KEY_3")   # optional
OTX_API_KEY = os.environ["OTX_API_KEY"]         # optional

MAIN_BACKEND_TOPIC = os.environ.get("MAIN_BACKEND_TOPIC", "entities")

guard = Guard().use_many(
    ToxicLanguage(threshold=0.5, validation_method="sentence", on_fail=OnFailAction.EXCEPTION),
    ProfanityFree(on_fail=OnFailAction.EXCEPTION),
)

if not OS_API_KEY:
    raise RuntimeError("OS_API_KEY not set. export OS_API_KEY=...")

print(f"[watchdog] Reading from: {INBOX_GLOB}")
print(f"[watchdog] Writing to: {WATCHDOG_DIR}")


# =============================================================================
# Ingestion: SAME CSV INPUT as main.py, but in STATIC mode
# =============================================================================

class EntitiesSchema(pw.Schema):
    # IMPORTANT: no primary_key in streaming
    entity_id: str
    face_match_urls: list[str]

    # Financial and Contact
    annual_income: str
    applicant_email: str
    applicant_mobile_number: str
    occupation: str
    sources_of_income: list[str] # LIST type
    
    # Applicant Identity
    applicant_name: str # Full name - first + middle + last single space separated
    
    date_of_birth: str
    gender: str
    marital_status: str
    nationality: str
    
    # Addresses
    current_address: str
    permanent_address: str
    residential_status: str
    
    # Identification Numbers
    passport_number: str
    unique_identification_number: str
    
    # Family Details (Parent/Guardian)
    father_name: str
    mother_name: str

rdkafka_settings = {
    "bootstrap.servers": os.environ.get("BOOTSTRAP_SERVERS", "localhost:9092"),
    "group.id": os.environ.get("GROUP_ID", "0"),
    "session.timeout.ms": os.environ.get("SESSION_TIMEOUT_MS", "6000"),
    "auto.offset.reset": os.environ.get("AUTO_OFFSET_RESET", "earliest"),
}

entities = pw.io.kafka.read( # should be static postgres
    rdkafka_settings,
    topic=MAIN_BACKEND_TOPIC,
    format="json",
    schema=EntitiesSchema,
    autocommit_duration_ms=100,
    mode="static"
)

raw_ingest = entities.select(
    entity_id       =   pw.this.entity_id, 
    name            =   pw.this.applicant_name, 
    gender          =   pw.this.gender,
)

pw.io.jsonlines.write(raw_ingest, str(WATCHDOG_DIR / "raw_ingest_initial.jsonl"))

# Add check timestamp to track when this re-evaluation happened
raw_ingest = raw_ingest.with_columns(
    check_timestamp     =   time.time()
)

pw.io.jsonlines.write(raw_ingest, str(WATCHDOG_DIR / "raw_ingest.jsonl"))

# =============================================================================
# Enrichment: OS lookup, then web+LLM (SAME as main.py)
# =============================================================================
enriched = raw_ingest.with_columns(
    _os             = os_lookup(pw.this.name),   # dict -> pw.Json
).with_columns(
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
    web_tuple      = run_web_analysis(pw.this.name, filename=str(OUT_DIR / "agent_web_articles.jsonl")),
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

# =============================================================================
# Run (Static mode - processes once and exits)
# =============================================================================
if __name__ == "__main__":
    log.info("Starting Pathway watchdog run (static mode)...")
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)
    log.info("Watchdog check completed successfully")