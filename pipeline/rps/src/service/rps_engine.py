import numpy as np
import pandas as pd
import joblib, os
from pathlib import Path
from rules.rule_engine import evaluate_rules
from rules.evidence import compute_evidence
from rules.compute_prior import compute_prior
import json

SRC_DIR = Path("rps/src/").resolve()

with open(SRC_DIR / "models/training_features.json") as f:
    TRAIN_FEATURES = json.load(f)


pml_model = joblib.load(SRC_DIR / "models/p_ml_model.pkl")
anomaly_model = joblib.load(SRC_DIR / "models/anomaly_model.pkl")
anomaly_scaler = joblib.load(SRC_DIR / "models/anomaly_scaler.pkl")
fusion_model = joblib.load(SRC_DIR / "models/fusion_model.pkl")


pi = compute_prior(SRC_DIR / "data/processed/features.parquet")


import json
with open(SRC_DIR / "models/lr_dict.json", "r") as f:
    lr_dict = json.load(f)

def logit(x, eps=1e-9):
    x = np.clip(x, eps, 1 - eps)
    return np.log(x / (1 - eps))

def compute_rps(features: dict):
    # Ensure we pass the exact training feature columns (in correct order)
    # to avoid sklearn warnings about unknown feature names.
    df = pd.DataFrame([features])
    try:
        # Reindex to TRAIN_FEATURES; missing columns will be filled with 0
        df = df.reindex(columns=TRAIN_FEATURES, fill_value=0)
    except Exception:
        # If TRAIN_FEATURES is not available or mismatch, fall back to original df
        pass

    # Convert all columns to numeric where possible; non-numeric become 0
    X = df.apply(pd.to_numeric, errors="coerce").fillna(0)
    p_ml = float(pml_model.predict_proba(X)[0][1])
    raw = float(anomaly_model.decision_function(X)[0])
    a = float(anomaly_scaler.transform([[raw]])[0][0])
    rule_hits = evaluate_rules(df.iloc[0])
    e = float(compute_evidence(rule_hits, lr_dict, pi))
    Xfusion = np.array([
        logit(p_ml), 
        logit(a), 
        e
    ]).reshape(1, -1)

    rps = float(fusion_model.predict_proba(Xfusion)[0][1])

    return {
        "p_ml": p_ml,
        "anomaly": a,
        "evidence": e,
        "rps": rps
    }

