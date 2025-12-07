import json
import re
import pathway as pw

@pw.udf
def to_lower(s: str | None) -> str | None:
    return s.lower().strip() if isinstance(s, str) else None

@pw.udf
def to_int_safe(s: str | None) -> int | None:
    try:
        return int(s) if s not in (None, "") else None
    except Exception:
        return None


@pw.udf
def json_to_float(x) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None

@pw.udf
def json_to_score_text(x) -> str:
    try:
        if x is None:
            return "N/A"
        return f"{float(x):.3f}"
    except Exception:
        # last-resort textualization
        try:
            return str(x)
        except Exception:
            return "N/A"
        
# UDF to parse the JSON string from the model's response
@pw.udf
def parse_json_score(json_string: str) -> float:
    try:
        json_string = json_string.strip()
        start = json_string.find('{')
        end = json_string.rfind('}') + 1
        
        if start == -1 or end == 0:
            return -1.0
            
        json_data = json.loads(json_string[start:end])
        return float(json_data.get('authenticity_score', -1.0)) 
    except Exception:
        return -1.0 
    
@pw.udf
def compute_risk_from_score(score: float | None) -> dict:
    if score is None:
        return {"risk_score": 0, "risk_classification": "LOW", "match_found": False}
    try:
        pct = max(0, min(100, int(round(float(score) * 100))))
    except Exception:
        pct = 0
    if pct >= 90: cls = "CRITICAL"
    elif pct >= 70: cls = "HIGH"
    elif pct >= 40: cls = "MEDIUM"
    else: cls = "LOW"
    return {"risk_score": pct, "risk_classification": cls, "match_found": pct > 0}

def extract_json_and_summary(s: str):

    json_pattern = r'```json\n(.*?)\n```'
    json_match = re.search(json_pattern, s, re.DOTALL)
    
    if json_match:
        json_str = json_match.group(1)
        parsed_json = json.loads(json_str)
    else:
        parsed_json = None
    
    # Extract SUMMARY (everything after "SUMMARY")
    summary_pattern = r'<SUMMARY>\n(.*)|SUMMARY\n(.*)'
    summary_match = re.search(summary_pattern, s, re.DOTALL)
    
    summary = summary_match.group(1) if summary_match else None
    
    return parsed_json, summary