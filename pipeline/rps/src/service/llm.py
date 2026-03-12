from datetime import time
import logging
import os
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import requests
from fastapi import FastAPI, HTTPException

import pathway as pw
from pathway.xpacks.llm import llms

load_dotenv()

OUT_DIR = Path("out").resolve()
FRAUD_TOPIC = os.environ.get("FRAUD_TOPIC", "possible_fraud")

SCORE_URL = os.getenv("SCORE_URL", "http://127.0.0.1:9000/score")
# LLM_URL = os.getenv("LLM_URL", "http://127.0.0.1:11434/v1/chat/completions")
# LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:1.5b")  

rdkafka_settings = {
    "bootstrap.servers": os.environ.get("BOOTSTRAP_SERVERS", "localhost:9092"),
    "group.id": os.environ.get("GROUP_ID", "0"),
    "session.timeout.ms": os.environ.get("SESSION_TIMEOUT_MS", "6000"),
    "auto.offset.reset": os.environ.get("AUTO_OFFSET_RESET", "earliest"),
}

model = llms.LiteLLMChat(
    model="mistral/mistral-small-latest", 
    api_key=os.environ["MISTRAL_KEY"], 
)

log = logging.getLogger("rps_360_pipeline")

class FeatureRequest(pw.Schema):
    user_id: str
    full_name: str
    # lightweight request schema (used by FastAPI endpoints if needed)
    # Detailed transaction features are defined in TransactionFeaturesSchema below.


class ScoreResponse(pw.Schema):
    p_ml: float
    anomaly: float
    evidence: float
    rps: float

def simple_risk_band(rps: float) -> str:
    if rps < 0.15:
        return "LOW"
    elif rps < 0.30:
        return "MEDIUM"
    else:
        return "HIGH"   

def call_xpack_llm(features: Dict[str, Any], scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Calls an XPack LLM (like Qwen) and expects JSON back.
    If JSON parsing fails, returns a safe fallback explanation.
    Features passed in should already contain only numeric fields (no user_id/full_name).
    """
    system_prompt = (
        "You are a senior fraud risk analyst. "
        "You receive transaction features and model scores: p_ml, anomaly, evidence, rps. "
        "Your job is ONLY to interpret these scores and describe risk. "
        "NEVER change the numeric scores. Do not guess new numbers. "
        "Respond in STRICT JSON ONLY with keys: "
        "\"risk_level\" (string), "
        "\"short_reason\" (string), "
        "\"long_reason\" (string), "
        "\"recommended_action\" (string), "
        "\"tags\" (array of strings). "
        "Do not add any extra keys. Do not wrap JSON in markdown. "
        "Strictly ONLY JSON FORMAT"
    )

    user_payload = {    
        "features": features,
        "scores": scores,
    }

    try:
        # Build a small Pathway table with the chat history and ask the model
        # via a computation graph, then extract the computed string synchronously
        # using pw.debug.table_to_dicts. This avoids getting an AsyncApplyExpression
        # object that cannot be JSON-parsed directly.
        # The model expects text content for messages. Serialize the payload
        # to a JSON string so the "user" content is a valid string.
        queries = pw.debug.table_from_rows(
            pw.schema_from_types(questions=list[dict]),
            rows=[([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],)],
        )

        # This returns a Table; the model expression is evaluated inside the table
        raw_responses = queries.select(raw_result=model(pw.this.questions))

        # Convert the Pathway Table into Python dicts and extract the raw string
        tbl_dicts = pw.debug.table_to_dicts(raw_responses)

        # tbl_dicts can vary across Pathway versions: it may be a tuple/list
        # (pointers, {col: {ptr: value}}), or a dict. Walk the structure to
        # find the first string value returned by the model.
        resp_str = None

        def find_string(obj):
            # Recursively find the first string value in nested structures.
            if obj is None:
                return None
            if isinstance(obj, str):
                return obj
            if isinstance(obj, (list, tuple)):
                for it in obj:
                    s = find_string(it)
                    if s:
                        return s
            if isinstance(obj, dict):
                for v in obj.values():
                    s = find_string(v)
                    if s:
                        return s
            return None

        resp_str = find_string(tbl_dicts)

        if resp_str is None:
            raise RuntimeError("Unable to extract model string from Pathway table result")

        # Strip common code fences (```json ... ```) and surrounding whitespace
        import re
        # remove ```json and ``` fences
        cleaned = re.sub(r"(?s)```\s*json\s*(.*?)```", r"\1", resp_str)
        cleaned = re.sub(r"(?s)```(.*?)```", r"\1", cleaned)
        cleaned = cleaned.strip()

        # If the model returned extra text, try to extract the first JSON object
        try:
            explanation = json.loads(cleaned)
        except Exception:
            m = re.search(r"(?s)(\{.*\})", cleaned)
            if m:
                try:
                    explanation = json.loads(m.group(1))
                except Exception as e:
                    raise RuntimeError(f"Failed to parse JSON from model output: {e}; cleaned output: {cleaned}")
            else:
                raise RuntimeError(f"Model output is not valid JSON and no JSON object found: {cleaned}")

    except Exception as e:
        rps = float(0.0)
        risk = simple_risk_band(rps)

        return {
            "risk_level": risk,
            "short_reason": f"LLM unavailable, using fallback. Overall risk band is {risk}.",
            "long_reason": "The LLM endpoint could not be reached or returned an error. "
                           "This explanation is generated by a simple rule-based fallback "
                           "using the rps score.",
            "recommended_action": "Use raw scores and internal rules. Investigate if necessary.",
            "tags": ["llm_error", "fallback"],
        }
    
    for key in ["risk_level", "short_reason", "long_reason", "recommended_action", "tags"]:
        if key not in explanation:
            if key == "tags":
                explanation[key] = ["llm_missing_key"]
            else:
                explanation[key] = f"[missing {key} from LLM]"

    
    if not isinstance(explanation.get("tags"), list):
        explanation["tags"] = [str(explanation.get("tags"))]

    return explanation


def call_score_service(features: Dict[str, Any]) -> Dict[str, float]:
    """
    Calls your existing scoring service at SCORE_URL.
    Expects JSON like: {"p_ml": ..., "anomaly": ..., "evidence": ..., "rps": ...}
    """
    try:
        resp = requests.post(SCORE_URL, json={"features": features}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error calling score service: {e}")

    try:
        scores = resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON from score service: {e}")

    
    for key in ["p_ml", "anomaly", "evidence", "rps"]:
        if key not in scores:
            raise HTTPException(
                status_code=500,
                detail=f"Score service response missing key '{key}': {scores}",
            )

    return scores


@pw.udf
def process_transaction_features(
    user_id: str,
    full_name: str,
    total_amount_1h: float,
    txn_count_1h: int,
    unique_cp_1h: int,
    avg_amount_1h: float,
    max_amount_1h: float,
    min_amount_1h: float,
    total_amount_24h: float,
    txn_count_24h: int,
    unique_cp_24h: int,
    avg_amount_24h: float,
    max_amount_24h: float,
    min_amount_24h: float,
    total_amount_7d: float,
    txn_count_7d: int,
    unique_cp_7d: int,
    avg_amount_7d: float,
    max_amount_7d: float,
    min_amount_7d: float,
    total_amount_30d: float,
    txn_count_30d: int,
    unique_cp_30d: int,
    avg_amount_30d: float,
    max_amount_30d: float,
    min_amount_30d: float,
    incoming_outgoing_ratio_7d: float,
) -> dict:
    """
    Process transaction features through scoring and LLM explanation pipeline.
    Returns dict with scores and LLM explanation as separate fields.
    """
    # Build dict of numeric features ONLY (no user_id/full_name)
    # This matches the training features expected by the scoring model
    features_to_pass = {
        "total_amount_1h": total_amount_1h,
        "txn_count_1h": txn_count_1h,
        "unique_cp_1h": unique_cp_1h,
        "avg_amount_1h": avg_amount_1h,
        "max_amount_1h": max_amount_1h,
        "min_amount_1h": min_amount_1h,
        "total_amount_24h": total_amount_24h,
        "txn_count_24h": txn_count_24h,
        "unique_cp_24h": unique_cp_24h,
        "avg_amount_24h": avg_amount_24h,
        "max_amount_24h": max_amount_24h,
        "min_amount_24h": min_amount_24h,
        "total_amount_7d": total_amount_7d,
        "txn_count_7d": txn_count_7d,
        "unique_cp_7d": unique_cp_7d,
        "avg_amount_7d": avg_amount_7d,
        "max_amount_7d": max_amount_7d,
        "min_amount_7d": min_amount_7d,
        "total_amount_30d": total_amount_30d,
        "txn_count_30d": txn_count_30d,
        "unique_cp_30d": unique_cp_30d,
        "avg_amount_30d": avg_amount_30d,
        "max_amount_30d": max_amount_30d,
        "min_amount_30d": min_amount_30d,
        "incoming_outgoing_ratio_7d": incoming_outgoing_ratio_7d,
    }
    
    try:
        scores = call_score_service(features_to_pass)
        explanation = call_xpack_llm(features_to_pass, scores)
        
        return {
            "user_id": user_id,
            "full_name": full_name,
            "p_ml": scores.get("p_ml"),
            "anomaly": scores.get("anomaly"),
            "evidence": scores.get("evidence"),
            "rps": scores.get("rps"),
            "risk_level": explanation.get("risk_level"),
            "short_reason": explanation.get("short_reason"),
            "long_reason": explanation.get("long_reason"),
            "recommended_action": explanation.get("recommended_action"),
            "tags": json.dumps(explanation.get("tags", [])),
        }
    except Exception as e:
        # Return error response with None values
        return {
            "user_id": user_id,
            "full_name": full_name,
            "p_ml": None,
            "anomaly": None,
            "evidence": None,
            "rps": None,
            "risk_level": None,
            "short_reason": None,
            "long_reason": None,
            "recommended_action": str(e),
            "tags": json.dumps(["error"]),
        }


class TransactionFeaturesSchema(pw.Schema):
    user_id: int
    full_name: str
    total_amount_1h: float
    txn_count_1h: int
    unique_cp_1h: int
    avg_amount_1h: float
    max_amount_1h: float
    min_amount_1h: float
    total_amount_24h: float
    txn_count_24h: int
    unique_cp_24h: int
    avg_amount_24h: float
    max_amount_24h: float
    min_amount_24h: float
    total_amount_7d: float
    txn_count_7d: int
    unique_cp_7d: int
    avg_amount_7d: float
    max_amount_7d: float
    min_amount_7d: float
    total_amount_30d: float
    txn_count_30d: int
    unique_cp_30d: int
    avg_amount_30d: float
    max_amount_30d: float
    min_amount_30d: float
    incoming_outgoing_ratio_7d: float


transactions = pw.io.kafka.read(
    rdkafka_settings,
    topic="rps_processed_features",
    schema=TransactionFeaturesSchema,
    autocommit_duration_ms=100,
    format="json",
)

pw.io.jsonlines.write(transactions, OUT_DIR / "transactions_debug.jsonl")

# Helper UDF to extract dict values into separate columns
@pw.udf
def extract_result(result_dict: dict) -> tuple:
    """Extract all fields from result dict into a tuple for unpacking."""
    return (
        result_dict.get("user_id"),
        result_dict.get("full_name"),
        result_dict.get("p_ml"),
        result_dict.get("anomaly"),
        result_dict.get("evidence"),
        result_dict.get("rps"),
        result_dict.get("risk_level"),
        result_dict.get("short_reason"),
        result_dict.get("long_reason"),
        result_dict.get("recommended_action"),
        result_dict.get("tags"),
    )

# Process each transaction through the scoring and LLM pipeline
result_dict = transactions.select(
    result=process_transaction_features(
        pw.this.user_id,
        pw.this.full_name,
        pw.this.total_amount_1h,
        pw.this.txn_count_1h,
        pw.this.unique_cp_1h,
        pw.this.avg_amount_1h,
        pw.this.max_amount_1h,
        pw.this.min_amount_1h,
        pw.this.total_amount_24h,
        pw.this.txn_count_24h,
        pw.this.unique_cp_24h,
        pw.this.avg_amount_24h,
        pw.this.max_amount_24h,
        pw.this.min_amount_24h,
        pw.this.total_amount_7d,
        pw.this.txn_count_7d,
        pw.this.unique_cp_7d,
        pw.this.avg_amount_7d,
        pw.this.max_amount_7d,
        pw.this.min_amount_7d,
        pw.this.total_amount_30d,
        pw.this.txn_count_30d,
        pw.this.unique_cp_30d,
        pw.this.avg_amount_30d,
        pw.this.max_amount_30d,
        pw.this.min_amount_30d,
        pw.this.incoming_outgoing_ratio_7d,
    ),
)
# Unpack result dict into separate columns
rps_output = result_dict.select(
    user_id=pw.this.result["user_id"].as_int(),
    full_name=pw.this.result["full_name"].as_str(),
    p_ml=pw.this.result["p_ml"].as_float(),
    anomaly=pw.this.result["anomaly"].as_float(),
    evidence=pw.this.result["evidence"].as_float(),
    rps=pw.this.result["rps"].as_float(),
    risk_level=pw.this.result["risk_level"].as_str(),
    short_reason=pw.this.result["short_reason"].as_str(),
    long_reason=pw.this.result["long_reason"].as_str(),
    recommended_action=pw.this.result["recommended_action"].as_str(),
    tags=pw.this.result["tags"],
)

pw.io.jsonlines.write(rps_output, OUT_DIR / "rps_output.jsonl")
pw.io.kafka.write(
    rps_output,
    rdkafka_settings,
    topic_name=FRAUD_TOPIC,
    format="json",
)

def clean_persistent_storage():
    if os.path.exists("./RPSState"):
        shutil.rmtree("./RPSState")

if __name__ == "__main__":
    log.info("Starting Pathway streaming run...")

    # clears the storage file created
    # clean_persistent_storage()

    # Change: persistence config created
    backend = pw.persistence.Backend.filesystem("./RPSState")
    persistence_config = pw.persistence.Config(backend)
    
    pw.run(
        monitoring_level=pw.MonitoringLevel.NONE, # no MonitoringMode / autocommit args in your version
        persistence_config=persistence_config, # Change: persistence config passed to the method
    )
