# main.py

"""
DID OPEN SANCTIONS ENRICHMENT WITH EXTRA FIELDS FROM THE KYC FORM
NEED TO TEST AND EXTEND MORE IN THE PIPELINE

"""


from __future__ import annotations

import os
import profile
import time
import logging
from dotenv import load_dotenv
from pathlib import Path
from guardrails import Guard, OnFailAction
from guardrails.hub import ToxicLanguage, ProfanityFree 

import pathway as pw
from pathway.xpacks.llm import llms

# ---------- optional helpers you already have ----------
from utils.llm_output import generate_content, make_llm_prompt, parse_raw_llm_text, run_web_analysis
from utils.open_sanctions import os_lookup
from utils.utils import compute_risk_from_score

# =============================================================================
# Config & Logging
# =============================================================================
load_dotenv()

def _abs_glob(glob_str: str) -> str:
    p = Path(os.path.expanduser(glob_str))
    parent = p.parent.resolve()
    return str(parent / p.name)

# kafka topics
DB_TOPIC = os.environ.get("DB_TOPIC", "db_updates")
MAIN_BACKEND_TOPIC = os.environ.get("MAIN_BACKEND_TOPIC", "entities")

INBOX_GLOB = _abs_glob("inbox/*.csv")
OUT_DIR = Path("out").resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("pathway_pipeline")

OS_API_KEY=os.environ["OS_API_KEY"]           # required
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")   # optional
OTX_API_KEY = os.environ["OTX_API_KEY"]         # optional
MISTRAL_KEY = os.environ["MISTRAL_KEY"]         # optional

model = llms.LiteLLMChat(
    model="mistral/mistral-small-latest", 
    api_key=MISTRAL_KEY, 
)

guard = Guard().use_many(
    ToxicLanguage(threshold=0.5, validation_method="sentence", on_fail=OnFailAction.EXCEPTION),
    ProfanityFree(on_fail=OnFailAction.EXCEPTION),
)

if not OS_API_KEY:
    raise RuntimeError("OS_API_KEY not set. `export OS_API_KEY=...`")

print(f"[streaming] Watching: {INBOX_GLOB}")
print(f"[streaming] Writing to: {OUT_DIR}")

# =============================================================================
# Ingestion: STREAMING CSVs
# =============================================================================
class EntitiesSchema(pw.Schema):
    # IMPORTANT: no primary_key in streaming
    entity_id: str
    face_match_urls: list[str]
    profile_pic: str

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

entities = pw.io.kafka.read(
    rdkafka_settings,
    topic=MAIN_BACKEND_TOPIC,
    format="json",
    schema=EntitiesSchema,
    autocommit_duration_ms=100,
)

pw.io.jsonlines.write(entities, str(OUT_DIR / "raw_ingest.jsonl"))

# just to keep a record of what we have here
# canonical = entities.with_columns(
    # entity_id        = pw.this.entity_id,
    # canonical_name   = pw.this.applicant_name,
    # face_match_urls  = pw.this.face_match_urls,
    # date_of_birth    = pw.this.date_of_birth,  # keep as str for now since date formats vary and depend on writing style. cant do strptime too
    # canonical_gender = pw.this.gender,
    # father_name      = pw.this.father_name,
    # mother_name      = pw.this.mother_name,
    # residential_status = pw.this.residential_status,
    # annual_income    = pw.this.annual_income,
    # applicant_email  = pw.this.applicant_email,
    # applicant_mobile_number = pw.this.applicant_mobile_number,
    # marital_status   = pw.this.marital_status,
    # current_address  = pw.this.current_address,
    # nationality      = pw.this.nationality,
    # occupation       = pw.this.occupation,
    # passport_number  = pw.this.passport_number,
    # permanent_address = pw.this.permanent_address,
    # sources_of_income = pw.this.sources_of_income,
    # unique_identification_number = pw.this.unique_identification_number
# )

# =============================================================================
# Enrichment: OS lookup, then web+LLM (optional)
# =============================================================================
enriched = entities.with_columns(
    _os             = os_lookup(pw.this.applicant_name, pw.this.date_of_birth, pw.this.nationality, pw.this.applicant_name),
).with_columns(
    os_entity_id    = pw.this._os["entity_id"],
    os_entity_name  = pw.this._os["entity_name"],
    os_score        = pw.this._os["score"],
    os_raw          = pw.this._os["data"],
)

# Append enriched matches
pw.io.jsonlines.write(enriched, str(OUT_DIR / "opensanctions_results.jsonl"))

with_web = enriched.with_columns(
    web_tuple      = run_web_analysis(pw.this.applicant_name, pw.this.face_match_urls),
).with_columns(
    web_prompt     = pw.this.web_tuple[0],
    citations      = pw.this.web_tuple[1],
)

pw.io.jsonlines.write(with_web, str(OUT_DIR / "web_analysis_debug.jsonl"))

llm_ready = with_web.with_columns(
    system_prompt  = make_llm_prompt(pw.this.applicant_name, pw.this.os_entity_name, pw.this.os_score, pw.this.web_prompt, pw.this.annual_income, pw.this.occupation, pw.this.sources_of_income, pw.this.marital_status, pw.this.nationality, pw.this.current_address)[0],
    user_prompt    = make_llm_prompt(pw.this.applicant_name, pw.this.os_entity_name, pw.this.os_score, pw.this.web_prompt, pw.this.annual_income, pw.this.occupation, pw.this.sources_of_income, pw.this.marital_status, pw.this.nationality, pw.this.current_address)[1],
    fallback_json  = compute_risk_from_score(pw.this.os_score),
)

llm_called = llm_ready.with_columns(
    llm_text       = generate_content(pw.this.system_prompt, pw.this.user_prompt), 
)

pw.io.jsonlines.write(llm_called, str(OUT_DIR / "llm_called_debug.jsonl"))

final_report = llm_called.with_columns(
    parsed         = parse_raw_llm_text(pw.this.llm_text),
    timestamp      = time.time(),
).with_columns(
    risk_json      = pw.this.parsed[0],   # dict -> pw.Json
    summary        = pw.this.parsed[1],
).without( # remove raw objects which have been parsed
    "_os",
    "web_tuple",
    "web_prompt",
    "system_prompt",
    "user_prompt",
    "fallback_json", # THIS IS NEVER USED
    "parsed",
    "os_raw" # not used anywhere in the pipeline in future
)
# WE DO NOT REMOVE llm_Text NOW TO ADD IT TO THE AUDIT TRAIL

# Append-only outputs
pw.io.jsonlines.write(final_report, str(OUT_DIR / "reports.jsonl"))
pw.io.jsonlines.write(
    llm_called.select(entity_id=pw.this.entity_id, name=pw.this.applicant_name, llm_text=pw.this.llm_text),
    str(OUT_DIR / "llm_debug.jsonl"),
)

# NOW THAT WE HAVE ADDED, WE CAN REMOVE IT
final_report = final_report.without("llm_text")  # remove llm text

# Optional: latest-per-entity snapshot (compatible with your Pathway version)
latest = final_report.groupby(pw.this.entity_id).reduce(
    entity_id      = pw.this.entity_id,
    name           = pw.reducers.latest(pw.this.applicant_name),
    os_entity_name = pw.reducers.latest(pw.this.os_entity_name),
    os_score       = pw.reducers.latest(pw.this.os_score),
    risk_json      = pw.reducers.latest(pw.this.risk_json),
    summary        = pw.reducers.latest(pw.this.summary),
    citations      = pw.reducers.latest(pw.this.citations),
    timestamp      = pw.reducers.max(pw.this.timestamp),
)
pw.io.fs.write(latest, filename=str(OUT_DIR / "latest.jsonl"), format="json")

pw.io.kafka.write( # schema written is at the beginning of database_update.py
    final_report,
    rdkafka_settings,
    topic_name=DB_TOPIC,
    format="json",
)

# =============================================================================
# Run (Pathway versions without MonitoringMode/autocommit use bare run())
# =============================================================================
if __name__ == "__main__":
    log.info("Starting Pathway streaming run...")
    if os.path.exists(str(OUT_DIR / "scraped_web_articles.jsonl")):
        os.remove(str(OUT_DIR / "scraped_web_articles.jsonl"))
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)  # no MonitoringMode / autocommit args in your version
