# compliance_data_reader.py
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import datetime

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / f"pathway_datagetter_{datetime.datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("pathway_pipeline")

def read_scraped_articles(filename: str = "scraped_web_articles.jsonl") -> List[Dict[str, Any]]:
    """Reads JSON Lines of pre-scraped articles (each line is a JSON object)."""
    articles: List[Dict[str, Any]] = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    articles.append(json.loads(ln))
                except Exception:
                    logger.warning("Skipping malformed JSONL line.")
    except FileNotFoundError:
        logger.warning("Scraped file '%s' not found.", filename)
    except Exception as e:
        logger.error("Error reading scraped file '%s': %s", filename, e)
    return articles
