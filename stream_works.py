# stream_smoke.py
import os
from pathlib import Path
import pathway as pw

INBOX_DIR = Path(os.getenv("INBOX_DIR", "inbox")).resolve()
OUT_DIR   = Path(os.getenv("OUT_DIR", "out")).resolve()
INBOX_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

INBOX_GLOB = str(INBOX_DIR / "*.csv")
print(f"[smoke] Watching: {INBOX_GLOB}")
print(f"[smoke] Writing to: {OUT_DIR}")

class S(pw.Schema):
    entity_id: str = pw.column_definition(primary_key=True)
    name: str
    age: str | None
    gender: str | None

entities = pw.io.csv.read(INBOX_GLOB, schema=S, mode="streaming")

# raw passthrough sink
raw = entities.select(
    entity_id=pw.this.entity_id,
    name=pw.this.name,
    age=pw.this.age,
    gender=pw.this.gender,
)
pw.io.jsonlines.write(raw, str(OUT_DIR / "raw_ingest.jsonl"))

if __name__ == "__main__":
    pw.run(monitoring_mode=pw.MonitoringMode.OPTIMISTIC, autocommit_duration_ms=500)
