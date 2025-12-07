# Copyright © 2025 Pathway

from __future__ import annotations

import csv
import json
import logging
import os
import sys

from adverse_media_finder import scrape
# from scraping_python import scrape_articles


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

    # def run(self) -> None:
    #     for article in scrape_articles(
    #         self._website_urls,
    #         refresh_interval=self._refresh_interval,
    #     ):
    #         url = article["url"]
    #         text = article["text"]
    #         metadata = article["metadata"]

    #         self.next(url=url, text=text, metadata=metadata)
    
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

# # --- Command-line input handling ---
# if len(sys.argv) < 2:
#     print("Usage: python adverse_media_finder.py <csv_file>")
#     print("Example: python adverse_media_finder.py people.csv")
#     sys.exit(1)

# csv_file = sys.argv[1]

# # Check if file exists
# if not os.path.isfile(csv_file):
#     print(f"Error: File '{csv_file}' not found.")
#     sys.exit(1)

# Extract names from CSV
# kyc_names = []
# try:
#     with open(csv_file, 'r', encoding='utf-8') as f:
#         csv_reader = csv.DictReader(f)
#         if csv_reader.fieldnames is None or 'name' not in csv_reader.fieldnames:
#             print("Error: CSV file must contain a 'name' column.")
#             sys.exit(1)
        
#         for row in csv_reader:
#             name = row['name'].strip()
#             if name:  # Only add non-empty names
#                 kyc_names.append(name)
# except Exception as e:
#     print(f"Error reading CSV file: {e}")
#     sys.exit(1)

# if not kyc_names:
#     print("Error: No names found in the 'name' column.")
#     sys.exit(1)

# print(f"Loaded {len(kyc_names)} name(s) from '{csv_file}'.")

def sanitize(article):
    for k, v in article["metadata"].items():
        if hasattr(v, "isoformat"):
            article["metadata"][k] = v.isoformat()
    return article

# if __name__ == "__main__":
    # print(kyc_names)

def run_scraper(kyc_name : str, filename = "scraped_web_articles.jsonl"):
    # kyc_names = []
    # try:
    #     with open(csv_file, 'r', encoding='utf-8') as f:
    #         csv_reader = csv.DictReader(f)
    #         if csv_reader.fieldnames is None or 'name' not in csv_reader.fieldnames:
    #             print("Error: CSV file must contain a 'name' column.")
    #             sys.exit(1)
            
    #         for row in csv_reader:
    #             name = row['name'].strip()
    #             if name:  # Only add non-empty names
    #                 kyc_names.append(name)
    # except Exception as e:
    #     print(f"Error reading CSV file: {e}")
    #     sys.exit(1)

    # if not kyc_names:
    #     print("Error: No names found in the 'name' column.")
    #     sys.exit(1)

    # print(f"Loaded {len(kyc_names)} name(s) from '{csv_file}'.")

    # for kyc_name in kyc_names:
        print(f"Searching adverse media for: {kyc_name}")
        websites = scrape(kyc_name)


        import json
        with open(filename, "a") as f:
            for article in fetch_articles_from_urls(websites):
                f.write(json.dumps(sanitize(article), ensure_ascii=False) + "\n")  