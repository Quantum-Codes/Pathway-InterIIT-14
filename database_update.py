import pathway as pw
from pathlib import Path
from utils import to_int_safe, json_to_float
import os
"""
WARNING:
pathway.engine.EngineError: query "INSERT INTO entities (entity_id,name,os_entity_name,os_score,risk_json,summary,citations,timestamp,time,diff) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)" failed: error serializing parameter 8: out of range integral type conversion attempted

in errors like this, in "parameter 8", this is 0 indexed, so they actually mean $9 parameter
"""

"""
TO DO:
DELETE ENUM FROM Users table schema into a string
THEN TEST AGAIN
"""
# kafka topics
DB_TOPIC = 'db_updates'
MAIN_BACKEND_TOPIC = 'entities'
OUT_DIR = Path(os.getenv("OUT_DIR", "out")).resolve()


class DBRecordsSchema(pw.Schema):
    # IMPORTANT: no primary_key in streaming
    entity_id: str
    name: str
    os_entity_name: str | None
    os_score: float | None
    risk_json: dict
    summary: str | None
    citations: list[str] | None
    timestamp: float | None
    # diff: int | None
    # time: int | None

rdkafka_settings = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "0",
    "session.timeout.ms": "6000",
    "auto.offset.reset": "earliest",
}

connection_string_parts = {
    "host": "localhost",
    "port": "5432",
    "dbname": "values_db",
    "user": "user",
    "password": "password",
}

entities = pw.io.kafka.read(
    rdkafka_settings,
    topic=DB_TOPIC,
    format="json",
    schema=DBRecordsSchema,
    autocommit_duration_ms=100,
)

# convert to table
entities = entities.select(
    entity_id      = to_int_safe(pw.this.entity_id),
    name           = pw.this.name,
    os_entity_name = pw.this.os_entity_name,
    os_score       = pw.this.os_score,
    risk_json      = pw.this.risk_json,
    summary        = pw.this.summary,
    citations      = pw.this.citations,
    timestamp      = pw.this.timestamp,
)

pw.io.jsonlines.write(entities, str(OUT_DIR / "entities_debug.jsonl"))

user = entities.select(
    user_id        = pw.this.entity_id,
    username       = pw.this.name,
    current_rps_not= pw.apply(float, pw.this.risk_json["risk_score"]),
    risk_category = pw.apply(str, pw.this.risk_json["risk_classification"]),
    created_at      = pw.apply(pw.DateTimeNaive, pw.this.timestamp),
    last_rps_calculation = pw.apply(pw.DateTimeNaive, pw.this.timestamp),
)

rps_history = entities.select(
    user_id = pw.this.entity_id,
    rps_not = pw.apply(float, pw.this.risk_json["risk_score"]),
    sanction_score = pw.this.os_score,
    calculated_at = pw.apply(pw.DateTimeNaive, pw.this.timestamp),
)

sanction_match = entities.select(
    user_id = pw.this.entity_id,
    match_found = pw.apply(bool, pw.this.risk_json["match_found"]),
    match_confidence = pw.this.os_score,
    checked_at = pw.apply(pw.DateTimeNaive, pw.this.timestamp),
    matched_entity_name = pw.this.os_entity_name
)

try:
    pw.io.postgres.write(
        user,
        connection_string_parts,
        table_name="Users",

    )
    pw.io.postgres.write(
        rps_history,
        connection_string_parts,
        table_name="ToxicityHistory"
    )
    pw.io.postgres.write(
        sanction_match,
        connection_string_parts,
        table_name="UserSanctionMatches"
    )
except Exception as e: # duplicate key
    print(e)
    print("AAAAAAAAAAAAAAAAAAAAAAA")

pw.run(monitoring_level=pw.MonitoringLevel.NONE)
