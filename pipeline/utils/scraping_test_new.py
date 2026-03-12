# Copyright © 2025 Pathway

from __future__ import annotations
import logging

from utils.adverse_media_finder import scrape

import pathway as pw
from pathway.io.python import ConnectorSubject

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

import logging
from newspaper import Article
from newsplease import NewsPlease

def fetch_articles_from_urls(website_urls: list[str]):
    for url in website_urls:
        logging.info(f"Fetching: {url}")

        try:
            article = NewsPlease.from_url(url)
            if article and article.text:
                yield {
                    "url": url,
                    "text": article.text,
                    "metadata": {
                        "title": article.title,
                        "authors": article.authors,
                        "date_publish": article.date_publish,
                        "source_domain": article.source_domain,
                    },
                }
                continue  # successful → move to next URL

        except Exception:
            pass

        # fallback to newspaper3k if NewsPlease failed
        try:
            art = Article(url)
            art.download()
            art.parse()

            yield {
                "url": url,
                "text": art.text,
                "metadata": {
                    "title": art.title,
                    "authors": art.authors,
                    "publish_date": art.publish_date,
                },
            }

        except Exception as e:
            logging.error(f"Failed to fetch article: {url} | {e}")
            yield {
                "url": url,
                "text": "",
                "metadata": {"error": str(e)},
            }




class NewsScraperSubject(ConnectorSubject):
    _website_urls: list[str]
    _refresh_interval: int

    def __init__(
        self,
        *,
        website_urls: list[str],
        refresh_interval: int,
    ) -> None:
        super().__init__()
        self._website_urls = website_urls
        self._refresh_interval = refresh_interval

    def run(self) -> None:
        for article in fetch_articles_from_urls(self._website_urls):
            self.next(
                url=article["url"],
                text=article["text"],
                metadata=article["metadata"],
            )


class ConnectorSchema(pw.Schema):
    url: str = pw.column_definition(primary_key=True)
    text: str
    metadata: dict

def sanitize(article):
    for k, v in article["metadata"].items():
        if hasattr(v, "isoformat"):
            article["metadata"][k] = v.isoformat()
    return article

def run_scraper(kyc_name : str, face_match_urls: list[str] = []):
        print(f"Searching adverse media for: {kyc_name}")
        websites = scrape(kyc_name)
        websites.extend(face_match_urls)


        import json
        with open("out/scraped_web_articles.jsonl", "a") as f:
            for article in fetch_articles_from_urls(websites):
                f.write(json.dumps(sanitize(article), ensure_ascii=False) + "\n")  
