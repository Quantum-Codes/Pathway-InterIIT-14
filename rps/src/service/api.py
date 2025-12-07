from fastapi import FastAPI
from pydantic import BaseModel
from service.rps_engine import compute_rps

app = FastAPI()

class Snapshot(BaseModel):
    features: dict

@app.post("/score")
def score(snapshot: Snapshot):
    return compute_rps(snapshot.features)

