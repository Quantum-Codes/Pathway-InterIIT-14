# scheduler.py
"""
Scheduler that runs the watchdog every 10 minutes to re-evaluate existing entities.
The watchdog reads from the SAME CSV files as main.py but processes them in static mode.
"""
import ast
import json
import os
from typing import Union
from pydash import random
import time
import random
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import shutil
from dotenv import load_dotenv
import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.utils import extract_json_and_summary


# =============================================================================
# Config
# =============================================================================
load_dotenv()
WATCHDOG_SCRIPT = "watcher/watchdog.py"
CHECK_INTERVAL_SECONDS = 10  # 10 seconds
OUT_DIR = Path("out").resolve()
WATCHDOG_DIR = OUT_DIR / "watchdog"

T_min = 10 * 60       # seconds (10 minutes)
T = 10 * 60          # initial 10 minutes
T_max = 120 * 60     # seconds (2 hours)
beta = 0.7           # multiplicative decrease on write
gamma = 1.2          # multiplicative increase on idle
K_no_write = 3       # require 3 consecutive no-writes to increase
consecutive_no_write = 0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("scheduler")

app_host = "0.0.0.0" # Use 127.0.0.1 if running locally
app_port = 8000
api_url = f"http://{app_host}:{app_port}/v2/answer"

connection_string_parts = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
    "dbname": os.environ.get("POSTGRES_DBNAME", "values_db"),
    "user": os.environ.get("POSTGRES_USER", "user"),
    "password": os.environ["POSTGRES_PASSWORD"],
}

conn = psycopg2.connect(
    host=connection_string_parts["host"],
    port=connection_string_parts["port"],
    dbname=connection_string_parts["dbname"],
    user=connection_string_parts["user"],
    password=connection_string_parts["password"]
)
cursor = conn.cursor()

# =============================================================================
# Scheduler
# =============================================================================
def run_watchdog():
    """Execute the watchdog script."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info(f"{'='*60}")
    log.info(f"Running watchdog at {timestamp}")
    log.info(f"{'='*60}")
    
    try:
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, WATCHDOG_SCRIPT],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            log.info(f"✓ Watchdog completed successfully in {elapsed_time:.2f} seconds")
            if result.stdout:
                # Print key lines from output
                for line in result.stdout.split('\n'):
                    if '[watchdog]' in line or 'INFO' in line:
                        log.info(f"  {line}")
        else:
            log.error(f"✗ Watchdog failed with return code {result.returncode}")
            if result.stderr:
                log.error(f"STDERR: {result.stderr}")
            if result.stdout:
                log.error(f"STDOUT: {result.stdout}")
                
    except subprocess.TimeoutExpired:
        log.error("Watchdog execution timed out after 10 minutes")
    except Exception as e:
        log.error(f"Error running watchdog: {e}")
    
    # Log output file statistics
    try:
        reports_file = WATCHDOG_DIR / "reports.jsonl"
        if reports_file.exists():
            line_count = sum(1 for _ in open(reports_file))
            log.info(f"  Total reports in watchdog: {line_count}")
    except Exception as e:
        log.debug(f"Could not read report stats: {e}")
        
        
def _preprocess_text(text):
        """Preprocess text for semantic comparison"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', str(text).lower().strip())
        return text

def _calculate_cosine_similarity(text1, text2):
    """Calculate cosine similarity between two texts"""
    if not text1 or not text2:
        return 0.0
    
    text1 = _preprocess_text(text1)
    text2 = _preprocess_text(text2)
    
    if not text1 or not text2:
        return 0.0
    
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        similarity_score = similarity_matrix[0][0]
        return round(similarity_score, 4)
    except Exception as e:
        print(f"Error calculating cosine similarity: {e}")
        return 0.0


def main():
    """Main scheduler loop."""
    global T, consecutive_no_write
    log.info("="*60)
    log.info("WATCHDOG SCHEDULER STARTED")
    log.info("="*60)
    log.info(f"Check interval: {T} seconds ({T/60:.1f} minutes)")
    log.info(f"Watchdog script: {WATCHDOG_SCRIPT}")
    log.info(f"Output directory: {WATCHDOG_DIR}")
    log.info(f"Press Ctrl+C to stop")
    log.info("="*60)
    
    run_count = 0
    file_id = 0
    try:
        while True:
            run_count += 1
            log.info(f"Clearing the file scraped_web_articles.jsonl for next run...")
            scraped_file = OUT_DIR / "agent_web_articles.jsonl"
            if os.path.exists(scraped_file):
                os.remove(scraped_file)
                log.info(f"  Removed existing file: {scraped_file}")
            else:
                log.info(f"  No existing file to remove: {scraped_file}")            

            
            web_prompt_prev = []
            web_prompt_current = []          
            
            if os.path.exists(OUT_DIR / "watchdog_current") and os.path.exists(OUT_DIR / "watchdog_prev"):
                log.info(f"Calculating changes in web prompts between current and previous runs...")
                current_file = OUT_DIR / "watchdog_current" / "web_analysis_debug.jsonl"
                prev_file = OUT_DIR / "watchdog_prev" / "web_analysis_debug.jsonl"
                extra_file = OUT_DIR / "reports.jsonl"
                if os.path.exists(current_file) and os.path.exists(prev_file) and os.path.exists(extra_file):
                    def _read_web_prompts(path):
                        prompts = []
                        with open(path, "r", encoding="utf-8") as fh:
                            for line in fh:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    record = json.loads(line)
                                except json.JSONDecodeError:
                                    # fallback if file contains Python-style dicts (not recommended)
                                    try:
                                        record = ast.literal_eval(line)
                                    except Exception:
                                        log.exception("Failed to parse JSONL line, skipping")
                                        continue
                                prompts.append(record.get("web_prompt", ""))
                        return prompts
                    
                    def _read_id(path):
                        ids = []
                        with open(path, "r", encoding="utf-8") as fh:
                            for line in fh:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    record = json.loads(line)
                                except json.JSONDecodeError:
                                    # fallback if file contains Python-style dicts (not recommended)
                                    try:
                                        record = ast.literal_eval(line)
                                    except Exception:
                                        log.exception("Failed to parse JSONL line, skipping")
                                        continue
                                ids.append(record.get("entity_id", ""))
                        return ids
                    
                    def _read_name(path):
                        names = []
                        with open(path, "r", encoding="utf-8") as fh:
                            for line in fh:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    record = json.loads(line)
                                except json.JSONDecodeError:
                                    # fallback if file contains Python-style dicts (not recommended)
                                    try:
                                        record = ast.literal_eval(line)
                                    except Exception:
                                        log.exception("Failed to parse JSONL line, skipping")
                                        continue
                                names.append(record.get("name", ""))
                        return names
                    
                    def _read_rps(path):
                        rps_scores = []
                        with open(path, "r", encoding="utf-8") as fh:
                            for line in fh:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    record = json.loads(line)
                                except json.JSONDecodeError:
                                    # fallback if file contains Python-style dicts
                                    try:
                                        record = ast.literal_eval(line)
                                    except Exception:
                                        log.exception("Failed to parse JSONL line, skipping")
                                        continue
                                
                                # Prefer nested field: risk_json.risk_score
                                val = None
                                risk_json = record.get("risk_json")
                                if isinstance(risk_json, dict):
                                    val = risk_json.get("risk_score")

                                # Fallbacks
                                if val is None:
                                    val = record.get("rps")
                                if val is None:
                                    val = record.get("risk_score")

                                # Coerce to float safely
                                try:
                                    rps_scores.append(float(val) if val is not None else 0.0)
                                except Exception:
                                    rps_scores.append(0.0)

                        return rps_scores
                    
                    web_prompt_current = _read_web_prompts(current_file)
                    web_prompt_prev = _read_web_prompts(prev_file)
                    ids = _read_id(current_file)
                    names = _read_name(current_file)
                    rps_scores = _read_rps(extra_file)
                    
                    for idx, (entity_id, name, curr, prev, rps_score) in enumerate(zip(ids, names, web_prompt_current, web_prompt_prev, rps_scores)):
                        similarity = _calculate_cosine_similarity(curr, prev)

                        if similarity < 0.9:
                            log.info(f"  [Current prompt]: {curr[:100]}...")
                            log.info(f"  [Previous prompt]: {prev[:100]}...")
                            log.info(f"  [Entity {entity_id}] with [Name {name}] Web prompt changed significantly (similarity: {similarity})")
                            # Provide context to RAG Agent
                            record = {
                                "entity_id": entity_id,
                                "name": name,
                                "rps_score": rps_score,
                                "web_prompt_old": prev,
                                "web_prompt_new": curr
                            }
                            if not os.path.exists("./data"):
                                os.makedirs("./data")
                                
                            if os.path.exists(f"./data/RAGInput{file_id}.jsonl"):
                                with open(f"./data/RAGInput{file_id}.jsonl", "r", encoding="utf-8") as fh:
                                    line_count = sum(1 for line in fh)

                                    if line_count <= 4:
                                        with open(f"./data/RAGInput{file_id}.jsonl", "a", encoding="utf-8") as fh:
                                            fh.write(f"{json.dumps(record)}\n") 
                                    else: 
                                        file_id += 1
                                        with open(f"./data/RAGInput{file_id}.jsonl", "a", encoding="utf-8") as fh:
                                            fh.write(f"{json.dumps(record)}\n")
                            else:
                                with open(f"./data/RAGInput{file_id}.jsonl", "a", encoding="utf-8") as fh:
                                    fh.write(f"{json.dumps(record)}\n")

                            query_text = f"""
You are a compliance analyst LLM. Using the structured data below, compute a single normalized risk_score between 0 and 1, a risk_classification, and whether a match was found. Follow the algorithm and output rules exactly.

INPUT FIELDS (expected formats)

* EntityID: id
* Entity: string
* PreviousRho0: numeric previous rho0 value in [0,1] (if present)

PARSING RULES

1. Parse Score01: if provided as percent (e.g. "85%"), convert to 0.85. If >1 and <=100, divide by 100. If missing, default to 0.
2. Extract Open Sanctions Count N from ScoreText by parsing any integer. If none found, set N = 0.
3. Validate authenticity values; clamp to [0,1]. If no WebNotes, treat as empty list.

WEB ANALYSIS CHANGE HANDLING (rho0 update)
* Purpose: when comparative old and new web analyses are supplied, update rho0 deterministically using the change in computed web evidence between the two analyses and the provided PreviousRho0.
* Partition WebNotes into two sets by analysis_version:
  - Old set = articles where analysis_version == "old"
  - New set = articles where analysis_version == "new"
  - Unmarked articles belong to the "current overall" pool and are used in the main web_evidence_score calculation below.
* If both Old and New sets are present:
  1. Compute web_evidence_score_old using only the Old set (apply the same article severity mapping and probabilistic union as defined below).
  2. Compute web_evidence_score_new using only the New set.
  3. Let delta_web = web_evidence_score_new - web_evidence_score_old.
  4. Update rho0_new = clamp(PreviousRho0 + delta_web, 0.0, 1.0).
* If only New set present (no Old set) but PreviousRho0 is provided:
  - Treat web_evidence_score_old as 0.0 and set rho0_new = clamp(PreviousRho0 + web_evidence_score_new, 0.0, 1.0).
* If PreviousRho0 is not provided, do not create or infer rho0 — proceed without rho0 update.
* Use rho0_new (if computed) only for downstream models or fields that require rho0; it does not change the final_risk_score fusion weights below unless explicitly consumed by downstream systems.

SCORE COMPONENTS
A. Sanctions component (sanction_score)

* Normalize N to [0,1] using: sanction_score = min(N / 5, 1.0)
* Rationale: 5+ confirmed sanctions indicates maximum sanctions risk; lower counts scale linearly.

B. Web evidence component (web_evidence_score)

* For each article compute article_severity by mapping its type (or infer from excerpt if type missing) to:

  * official_sanction -> 1.0
  * conviction -> 0.95
  * indictment/charges -> 0.85
  * regulatory_fine -> 0.7
  * credible_allegation -> 0.6
  * negative_media -> 0.3
  * rumour -> 0.1
  * other -> 0.2

* article_score = authenticity * article_severity (both in [0,1]).
* Combine multiple article_scores into web_evidence_score using probabilistic union:
  web_evidence_score = 1 - Π(1 - article_score_i) across all articles.
* If WebNotes empty, web_evidence_score = 0.
* Note: when computing web_evidence_score_old or web_evidence_score_new in the "WEB ANALYSIS CHANGE HANDLING" section, apply the exact same mapping and probabilistic union but only on the subset of articles for that version.

C. Match confidence component

* match_confidence = parsed Score01 in [0,1].

FUSION (final risk score)

* Use weighted sum:
  final_risk_score = sanction_score * 0.60 + web_evidence_score * 0.30 + match_confidence * 0.10
* Round final_risk_score to 3 decimal places and clamp to [0,1].

CLASSIFICATION RULES

* LOW:   0.000 <= score < 0.250
* MEDIUM:0.250 <= score < 0.500
* HIGH:  0.500 <= score < 0.750
* CRITICAL: score >= 0.750

MATCH FOUND

* match_found = true if final_risk_score > 0, else false.

OUTPUT FORMAT (strict)

* Produce exactly two sections, nothing else, with no extra commentary or fields:

<JSON>
{{"risk_score": <float 0..1 with 3 decimals>, "risk_classification": "<LOW|MEDIUM|HIGH|CRITICAL>", "match_found": <true|false>}}
<SUMMARY>
One paragraph (single paragraph only) that states the key numeric breakdown and the primary drivers. The paragraph must include:
- parsed Open Sanctions count N and sanction_score,
- web_evidence_score and number of contributing articles,
- match_confidence,
- the formula used and the final rounded risk_score and classification,
- the single strongest driver (e.g., "sanctions", "web evidence", or "match confidence").

Analyse the following entity information and provide the risk_score and risk_classification according to the rules mentioned:\n\n
EntityID: {entity_id}\n
Entity: {name}\n
PreviousRho0: {rps_score}\n\n
"""

                            # The JSON payload to send
                            payload = {
                                "prompt": query_text
                            }

                            rps_score_new = rps_score

                            try:
                                # Send the POST request to the Pathway RAG server
                                response = requests.post(
                                    api_url, 
                                    json=payload, 
                                    timeout=40 # Set a reasonable timeout
                                )
                                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)


                                # The response will contain the answer and potentially context documents
                                result = response.json()

                                to_parse = str(result['response'])
                                parsed_output = extract_json_and_summary(to_parse)

                                print("\n\n-------------\n\n")
                                print(type(to_parse))
                                print("\n\n-------------\n\n")
                                print(parsed_output[0])
                                print("\n\n-------------\n\n")
                                print(parsed_output[1])
                                print("\n\n-------------\n\n")
                            
                                print("Successfully received response.")
                                print("---")
                                # print(f"*Query:* {query_text}")
                                # print(f"*Answer:* {result.get('response', 'No answer found')}")
                                
                                rps_score_new = parsed_output[0].get("risk_score", rps_score)

                                # rps_score_new = result.get('response', rps_score)
                                # print(rps_score_new)
                                if rps_score_new == 0.000 or rps_score_new is None:
                                    rps_score_new = rps_score

                                cursor.execute("""
                                        UPDATE Users
                                        SET current_rps_not = %s, last_rps_calculation = NOW()
                                        WHERE user_id = %s
                                    """, (rps_score_new, entity_id))
                                conn.commit()
                                
                                print(f"Updated risk score for EntityID {entity_id} to {rps_score_new}")

                                # The 'docs' key usually contains the context retrieved
                                # retrieved_docs = result.get('docs', [])
                                # if retrieved_docs:
                                #     print(f"*Context Documents Used (Count):* {len(retrieved_docs)}")
                                    # You can inspect the first document if needed:
                                    # print(f"First Doc Content Snippet: {retrieved_docs[0].get('text')[:200]}...")

                            except requests.exceptions.RequestException as e:
                                print(f"An error occurred: {e}")

                            consecutive_no_write = 0
                            T = max(T_min, T * beta)

                            log.info(f" Updated scheduler interval T to {T} seconds")

                            time.sleep(1)
                                
                        else:
                            log.info(f"  [Entity {entity_id}] with [Name {name}] Web prompt unchanged (similarity: {similarity})")

                            consecutive_no_write += 1
                            if consecutive_no_write >= K_no_write:
                                T = min(T_max, T * gamma)
                                log.info(f" Updated scheduler interval T to {T} seconds")
                                consecutive_no_write = 0 # reset after growth

            run_watchdog()
            
            if run_count != 1:
                shutil.copytree(OUT_DIR / "watchdog_current", OUT_DIR / "watchdog_prev", dirs_exist_ok=True)

            shutil.copytree(OUT_DIR / "watchdog", OUT_DIR / "watchdog_current", dirs_exist_ok=True)
            
            next_run = datetime.now().timestamp() + T
            next_run_str = datetime.fromtimestamp(next_run).strftime("%Y-%m-%d %H:%M:%S")
            log.info(f"Next check at: {next_run_str} (in {T/60:.1f} minutes)")
            log.info("")
            
            time.sleep(T)
            
    except KeyboardInterrupt:
        log.info("")
        log.info("="*60)
        log.info(f"Scheduler stopped by user after {run_count} runs")
        log.info("="*60)
    except Exception as e:
        log.error(f"Scheduler error: {e}")
        raise


if __name__ == "__main__":
    main()