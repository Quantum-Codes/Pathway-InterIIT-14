from fastapi import FastAPI
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from service.rps_engine import compute_rps

app = FastAPI()

class Snapshot(BaseModel):
    features: dict

@app.post("/score")
def score(snapshot: Snapshot):
    return compute_rps(snapshot.features)

