# scheduler.py
"""
Scheduler that runs the watchdog every 10 minutes to re-evaluate existing entities.
The watchdog reads from the SAME CSV files as main.py but processes them in static mode.
"""
import os
import time
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import shutil

# =============================================================================
# Config
# =============================================================================
WATCHDOG_SCRIPT = "watchdog.py"
CHECK_INTERVAL_SECONDS = 120  # 10 minutes
OUT_DIR = Path(os.getenv("OUT_DIR", "out")).resolve()
WATCHDOG_DIR = OUT_DIR / "watchdog"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("scheduler")

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
        log.error("✗ Watchdog execution timed out after 10 minutes")
    except Exception as e:
        log.error(f"✗ Error running watchdog: {e}")
    
    # Log output file statistics
    try:
        reports_file = WATCHDOG_DIR / "reports.jsonl"
        if reports_file.exists():
            line_count = sum(1 for _ in open(reports_file))
            log.info(f"  Total reports in watchdog: {line_count}")
    except Exception as e:
        log.debug(f"Could not read report stats: {e}")
        
        
def _preprocess_text(self, text):
        """Preprocess text for semantic comparison"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', str(text).lower().strip())
        return text

def _calculate_cosine_similarity(self, text1, text2):
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
    log.info("="*60)
    log.info("WATCHDOG SCHEDULER STARTED")
    log.info("="*60)
    log.info(f"Check interval: {CHECK_INTERVAL_SECONDS} seconds ({CHECK_INTERVAL_SECONDS/60:.1f} minutes)")
    log.info(f"Watchdog script: {WATCHDOG_SCRIPT}")
    log.info(f"Output directory: {WATCHDOG_DIR}")
    log.info(f"Press Ctrl+C to stop")
    log.info("="*60)
    
    run_count = 0
    
    try:
        while True:
            run_count += 1
            log.info(f"Clearing the file scraped_web_articles.jsonl for next run...")
            scraped_file = "./agent_web_articles.jsonl"
            if os.path.exists(scraped_file):
                os.remove(scraped_file)
                log.info(f"  Removed existing file: {scraped_file}")
            else:
                log.info(f"  No existing file to remove: {scraped_file}")
            
            
            
            run_watchdog()
            
            if run_count != 1:
                shutil.copytree(f"./out/watchdog_curr",f"./out/watchdog_prev", dirs_exist_ok=True)

            shutil.copytree(f"./out/watchdog",f"./out/watchdog_curr", dirs_exist_ok=True)

            # if run_count == 2:
            #     shutil.move(f"./out/watchdog_curr",f"./out/watchdog_prev")
            #     shutil.copytree(f"./out/watchdog_prev",f"./out/watchdog_curr")

            # if run_count > 2:
            #     shutil.rmtree(f"./out/watchdog_prev", ignore_errors=True)
            
            # shutil.copy2("./out/watchdog",f"./out/watchdog_{run_count}")
            
            # shutil.rmtree(f"./out/watchdog_{run_count-1}", ignore_errors=True)
            
            next_run = datetime.now().timestamp() + CHECK_INTERVAL_SECONDS
            next_run_str = datetime.fromtimestamp(next_run).strftime("%Y-%m-%d %H:%M:%S")
            log.info(f"Next check at: {next_run_str} (in {CHECK_INTERVAL_SECONDS/60:.1f} minutes)")
            log.info("")
            
            time.sleep(CHECK_INTERVAL_SECONDS)
            
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