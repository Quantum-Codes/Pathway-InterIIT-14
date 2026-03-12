import json
import re
import pathway as pw
import hashlib, time
import pandas as pd

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
def to_float_safe(s: str | None) -> float | None:
    try:
        return float(s) if s not in (None, "") else None
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
def sha256_uin(input_str: str) -> str | None:
    if not input_str:
        return None
    return hashlib.sha256(input_str.encode('utf-8')).hexdigest()

@pw.udf
def sha256_signature(name: str, id: int) -> str:
    combined_str = name + str(id)
    return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()


@pw.udf
def try_parse_date(date_string: str) -> pw.DateTimeNaive | None:
    """
    Attempts to parse a date string using pandas, supporting DD-MM-YYYY or YYYY-MM-DD formats.
    Returns a pandas.Timestamp object (which is compatible with pw.DateTimeNaive) on success, or None on failure.
    
    Note: Pathway will now correctly wrap and serialize the pandas.Timestamp for the PostgreSQL DATE column.
    """
    if not date_string:
        return None
    
    # Pathway/Postgres default format (YYYY-MM-DD)
    try:
        # pd.to_datetime returns a pandas.Timestamp
        return pd.to_datetime(date_string, format='%Y-%m-%d', errors='raise')
    except ValueError:
        pass # Try the next format
        
    # Alternate format (DD-MM-YYYY)
    try:
        return pd.to_datetime(date_string, format='%d-%m-%Y', errors='raise')
    except ValueError:
        pass # Try the next format

    # If all parsing fails, log a warning and return None
    print(f"Warning: Could not parse date string: {date_string}")
    return None

@pw.udf
def get_current_naive_datetime(useless_time: int) -> pw.DateTimeNaive:
    current_time = time.time()
    # Convert to pandas Timestamp (which is compatible with pw.DateTimeNaive)
    return pd.to_datetime(current_time, unit='s')

'''
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
'''
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