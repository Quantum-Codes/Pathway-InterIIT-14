import profile
import pathway as pw
from pathlib import Path
from utils.utils import (
    to_int_safe,
    to_float_safe, 
    sha256_uin, 
    sha256_signature, 
    try_parse_date,
    get_current_naive_datetime
)
import os
from dotenv import load_dotenv
"""
WARNING:
pathway.engine.EngineError: query "INSERT INTO entities (entity_id,name,os_entity_name,os_score,risk_json,summary,citations,timestamp,time,diff) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)" failed: error serializing parameter 8: out of range integral type conversion attempted

in errors like this, in "parameter 8", this is 0 indexed, so they actually mean $9 parameter
"""

"""
TO DO:
DEFINE utils.to_float_safe like the int for non json floatstring and for json floatstring use pw.this.whateverjsonfield.as_float(default=whateverfloat)
"""
# kafka topics

load_dotenv()
DB_TOPIC = os.environ.get("DB_TOPIC", "db_updates")
OUT_DIR = Path("out").resolve()

class FinalReportSchema(pw.Schema):
    # ==========================================
    # 1. ORIGINAL INPUTS (Persisted)
    # ==========================================
    entity_id: str
    applicant_name: str
    profile_pic : str
    
    # Biometrics & Identity
    face_match_urls: list[str]
    date_of_birth: str
    gender: str
    marital_status: str
    nationality: str
    
    # Financial & Contact
    annual_income: str
    applicant_email: str
    applicant_mobile_number: str
    occupation: str
    sources_of_income: list[str]
    
    # Addresses
    current_address: str
    permanent_address: str
    residential_status: str
    
    # IDs & Parents
    passport_number: str
    unique_identification_number: str
    father_name: str
    mother_name: str

    # ==========================================
    # 2. ENRICHED & COMPUTED FIELDS (Remaining)
    # ==========================================
    # OpenSanctions (Note: os_raw and _os are gone)
    os_entity_id: str  | None
    os_entity_name: str | None
    os_score: float | None

    # Web Analysis (Note: web_tuple and web_prompt are gone)
    citations: dict | None  # Contains the links/references found
    
    # Final Results (Parsed from 'parsed' tuple, which is now gone)
    risk_json: dict  # The structured risk analysis
    summary: str | None        # The text summary
    timestamp: float    # Execution time

rdkafka_settings = {
    "bootstrap.servers": os.environ.get("BOOTSTRAP_SERVERS", "localhost:9092"),
    "group.id": os.environ.get("GROUP_ID", "0"),
    "session.timeout.ms": os.environ.get("SESSION_TIMEOUT_MS", "6000"),
    "auto.offset.reset": os.environ.get("AUTO_OFFSET_RESET", "earliest"),
}

connection_string_parts = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
    "dbname": os.environ.get("POSTGRES_DBNAME", "values_db"),
    "user": os.environ.get("POSTGRES_USER", "user"),
    "password": os.environ["POSTGRES_PASSWORD"],
}

entities = pw.io.kafka.read(
    rdkafka_settings,
    topic=DB_TOPIC,
    format="json",
    schema=FinalReportSchema,
    autocommit_duration_ms=100,
)

# convert to table
entities = entities.with_columns(
    entity_id      = to_int_safe(pw.this.entity_id),
    date_of_birth = try_parse_date(pw.this.date_of_birth)
)

pw.io.jsonlines.write(entities, str(OUT_DIR / "entities_debug.jsonl"))

user = entities.select(
    user_id        = pw.this.entity_id,
    username       = pw.this.applicant_name,
    profile_pic   = pw.this.profile_pic,
    rps_not        = to_float_safe(pw.this.risk_json["risk_score"]),
    rps_360        = 0.0,
    news_score = 0.0,
    transaction_score = 0.0,
    portfolio_score = 0.0,
    calculation_trigger = "register",
    risk_category = pw.apply(str, pw.this.risk_json["risk_classification"]),
    created_at      = get_current_naive_datetime(pw.this.timestamp),
    sanction_score = pw.if_else(pw.this.os_score != None, pw.this.os_score, 0.0),
    match_found = pw.apply(bool, pw.this.risk_json["match_found"]),
    match_confidence = pw.this.os_score,
    matched_entity_name = pw.this.os_entity_name,
    uin = pw.this.unique_identification_number,
    uin_hash = sha256_uin(pw.this.unique_identification_number),
    email = pw.this.applicant_email,
    phone = pw.this.applicant_mobile_number,
    date_of_birth = pw.this.date_of_birth,
    address = pw.this.current_address,                
    occupation = pw.this.occupation,
    annual_income = to_float_safe(pw.this.annual_income),
    kyc_status = 'PENDING_VERIFICATION',
    signature_hash = sha256_signature(pw.this.applicant_name, pw.this.entity_id),
    credit_score = None,
    blacklisted = None,
    blacklisted_at = None,
    current_rps_not = None,
    current_rps_360 = None,
)


try:    
    pw.io.postgres.write(
        user,
        connection_string_parts,
        table_name="Staging_Buffer",
    )
except Exception as e: # duplicate key
    print(e)
    print("AAAAAAAAAAAAAAAAAAAAAAA")

pw.run(monitoring_level=pw.MonitoringLevel.NONE)
