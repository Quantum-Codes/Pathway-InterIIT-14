import json
import os
import re
import pathway as pw
from pathway.xpacks.llm import llms
from dotenv import load_dotenv

from typing import List, Tuple
from guardrails import Guard, OnFailAction
from guardrails.hub import ToxicLanguage, ProfanityFree 

from utils.compliance_data_reader import read_scraped_articles
from utils.scraping_test_new import (
    run_scraper,
)
from utils.sus import analyze_article_authenticity_with_metadata, check_alienvault, check_domain_history
from utils.utils import extract_json_and_summary, parse_json_score

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")   # optional
OTX_API_KEY = os.getenv("OTX_API_KEY")         # optional

guard = Guard().use_many(
    ToxicLanguage(threshold=0.5, validation_method="sentence", on_fail=OnFailAction.EXCEPTION),
    ProfanityFree(on_fail=OnFailAction.EXCEPTION),
)

model = llms.LiteLLMChat(
    model="mistral/mistral-small-latest", 
    api_key=os.environ["MISTRAL_KEY"], 
)

@pw.udf(return_type=tuple[str, list[str]], deterministic=False)
def run_web_analysis(canonical_name: str, face_match_urls: list[str] = []) -> Tuple[str, list[str]]:
    """
    Reads pre-scraped articles; runs optional OTX & metadata checks for top hits;
    returns (prompt_text, citations_list).
    """

    run_scraper(canonical_name, face_match_urls)

    name = (canonical_name or "").strip()
    if not name:
        return "No name provided.", []

    articles = read_scraped_articles()  # may return []
    if not articles:
        return "No pre-scraped articles available.", []

    hits: List[dict] = []
    for art in articles:
        try:
            alienvault_alexa_rank = "unknown"
            alienvault_akamai_rank = "unknown"
            title = (art.get("metadata", {}) or {}).get("title", "") or ""
            text = (art.get("text") or "")[:500]
            url = art.get("url") or ""
            if (url and (re.search(name, title, re.IGNORECASE) or re.search(name, text, re.IGNORECASE))):
                av_hint = "Unknown"
                otx_pulses = 0
                otx_tags: List[str] = []
                try:
                    if OTX_API_KEY:
                        av = check_alienvault(url, OTX_API_KEY)
                        # print(av)
                        alienvault_alexa_rank = av['general']['validation'][0]['message']
                        alienvault_akamai_rank = av['general']['validation'][1]['message']
                        av_hint = (av.get("general", {}).get("validation", [{}])[0].get("message", "Unknown"))
                        summ = _summarize_otx(av)
                        otx_pulses, otx_tags = summ.get("pulses_count", 0), summ.get("tags", [])
                except Exception:
                    pass

                score_met = 0.0
                try:
                    met = analyze_article_authenticity_with_metadata(url)
                    score_met = float(met.get("score", 0.0))
                except Exception:
                    pass

                has_hist = False
                try:
                    hist = check_domain_history(url)
                    has_hist = bool(hist.get("has_history", False))
                except Exception:
                    pass

                system_message = (
                    "You are an expert news fact-checker and sentiment analyzer. Your task is to analyze "
                    "the provided **article URL and text** for its journalistic quality, coherence, and apparent authenticity. "
                    "The domain of the source is a critical factor: a well-known, established news publisher "
                    "should increase the score, while an obscure or known-unreliable domain should decrease it. "
                    "You must provide an 'authenticity_score' between **0.0** (completely unreliable/unstructured) "
                    "and **1.0** (highly reliable/well-structured news report) based on the URL's domain reputation, "
                    "clarity of facts, sources mentioned (e.g., CBI, ED, court rulings), and overall narrative structure. "
                    "Output the result in a single JSON object with the keys 'authenticity_score' (float) "
                    "and 'reasoning' (string). DO NOT include any other text outside the JSON block."
                )

                # Pass both the URL and the text to the model
                user_message = (
                    f"Analyze the following article and provide an authenticity score based on the system instructions.\n\n"
                    f"**ARTICLE URL:** {url}\n\n"
                    f"**ARTICLE TEXT:**\n{text}"
                    f"\n\n--- ADDITIONAL AUTHENTICITY CONTEXT ---\n"
                    f"Use these indicators to adjust the final score:\n"
                    f"- **Reputation Check (AlienVault):** Alexa Rank: {alienvault_alexa_rank} / Akamai Rank: {alienvault_akamai_rank}\n"
                    f"  *(Low/prominent rank (e.g., #1000) increases score, 'Unknown' or high rank reduces score.)*\n"
                    f"- **Content Signals Score:** {score_met}\n"
                    f"  *(This reflects author/date/links/schema presence. Higher score means better journalistic hygiene.)*\n"
                    f"- **Domain Age Check (Wayback):** Domain Has History: {has_hist}\n"
                    f"  *(A domain with history is less likely to be a fly-by-night misinformation site. 'True' increases score.)*\n"
                )

                try:
                    guard.validate(system_message)
                    guard.validate(user_message)
                except Exception as e:
                    print(f"Guardrails validation failed: {e}")
                    continue

                # Create the table with the structured chat history
                queries = pw.debug.table_from_rows(
                    pw.schema_from_types(questions=list[dict]),
                    rows=[
                        (
                            [
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": user_message},
                            ],
                        )
                    ],
                )

                # Ask Gemini to process the chat history
                raw_responses = queries.select(raw_result=model(pw.this.questions))

                responses = raw_responses.select(
                    authenticity_score=parse_json_score(pw.this.raw_result),
                    raw_response=pw.this.raw_result
                )

                output=pw.debug.table_to_dicts(responses)

                authenticity_score = list(output[1]['authenticity_score'].values())[0]

                raw_response_str = list(output[1]['raw_response'].values())[0]
                clean_json_str = re.sub(r"```json|```", "", raw_response_str).strip()
                parsed = json.loads(clean_json_str)
                reasoning = parsed.get("reasoning", None)

                try:
                    guard.validate(reasoning)
                except Exception as e:
                    print(f"Guardrails validation failed on reasoning: {e}")
                    continue
                
                hits.append({
                    "url": url,
                    "title": title,
                    "score_met": authenticity_score,
                    "reasoning": reasoning,
                    "av_hint": av_hint,
                    "otx_pulses": otx_pulses,
                    "otx_tags": otx_tags,
                    "has_history": has_hist,
                    "snippet": (art.get("text") or "")[:160],
                })
        except Exception as e:
            print(f"\n\n {e} \n\n")
            continue

    if not hits:
        return f"No relevant web articles found for {name}.", []

    hits.sort(key=lambda x: (x["score_met"], x["has_history"], x["otx_pulses"]), reverse=True)
    top = hits[:3]
    citations = [f"- [{i+1}] {h['url']}" for i, h in enumerate(top)]
    blocks = []
    for i, h in enumerate(top):
        blocks.append(
            f"--- Article {i+1} ---\n"
            f"Title: {h['title']}\n"
            f"URL: {h['url']}\n"
            f"Authenticity Score: {h['score_met']:.2f} "
            f"(Reasoning: {h['reasoning']})\n"
            f"(History: {h['has_history']}, AlienVaultHint: {h['av_hint']}, "
            f"OTX pulses: {h['otx_pulses']}, OTX tags: {', '.join(h['otx_tags'])})\n"
            f"Snippet: {h['snippet']}..."
        )
    summary_prompt = f"Web findings for **{name}**:\n\n" + "\n\n".join(blocks)
    return summary_prompt, citations

def _summarize_otx(av: dict) -> dict:
    """Local summarizer to avoid relying on sus.summarize_otx existing."""
    pulses = av.get("pulse_info", {})
    plist = pulses.get("pulses") or []
    tags = set()
    for p in plist:
        for t in p.get("tags") or []:
            tags.add(str(t))
    return {"pulses_count": len(plist), "tags": sorted(tags)}

@pw.udf
def make_llm_prompt(name: str, os_entity_name: str | None, score_txt: str, web_prompt: str,
                   annual_income: str | None, occupation: str | None, sources_of_income: list[str], 
                   marital_status: str | None, nationality: str | None, current_address: str | None
                   ) -> Tuple[str, str]:
    match_name = os_entity_name or "None"
    return (
"""
You are a compliance analyst LLM. Using the structured data below, compute a single *normalized risk_score between 0 and 1*, a risk_classification, and whether a match was found. Follow the algorithm and output rules exactly.

INPUT FIELDS (expected formats)

* Entity: string
* TopMatch: string
* Score01: numeric match confidence between 0 and 1 (or percent — see parsing rules)
* ScoreText: Open Sanctions Score (number of sanctions, may appear as integer or as text containing digits)
* WebNotes: JSON array of scraped articles. Each WebNote object may include:

  * title: string
  * excerpt: string (short scraped text)
  * authenticity: numeric between 0 and 1 (trust score for that article)
  * source: string
  * date: ISO date (if available)
  * type: one of ["official_sanction","conviction","indictment","regulatory_fine","credible_allegation","negative_media","rumour","other"] if available

ADDITIONAL ENTITY CONTEXT (for match validation and contextual assessment)
* Annual Income: string
* Occupation: string
* Sources of Income: list of strings
* Marital Status: string
* Nationality: string
* Current Address: string

PARSING RULES

1. Parse Score01: if provided as percent (e.g. "85%"), convert to 0.85. If >1 and <=100, divide by 100. If missing, default to 0.
2. Extract Open Sanctions Count N from ScoreText by parsing any integer. If none found, set N = 0.
3. Validate authenticity values; clamp to [0,1]. If no WebNotes, treat as empty list.
4. Use Additional Entity Context to validate matches and provide contextual insights but DO NOT directly modify the calculated scores.
5. If any of additional entity context values is None, then it means we do not have that information about the entity so do not use that specific field in any way.

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
{"risk_score": <float 0..1 with 3 decimals>, "risk_classification": "<LOW|MEDIUM|HIGH|CRITICAL>", "match_found": <true|false>}
<SUMMARY>
One paragraph (single paragraph only) that states the key numeric breakdown and the primary drivers. The paragraph must include:
- parsed Open Sanctions count N and sanction_score,
- web_evidence_score and number of contributing articles,
- match_confidence,
- the formula used and the final rounded risk_score and classification,
- the single strongest driver (e.g., "sanctions", "web evidence", or "match confidence").
- Note any relevant entity context (e.g., high-risk nationality, suspicious occupation) that supports the assessment.
"""
    , 
        "Analyse the following entity information and provide the risk_score and risk_classification according to the rules mentioned:\n\n"
        f"Entity: {name}\n"
        f"TopMatch: {match_name}\n"
        f"Score01: {score_txt}\n"
        f"Entity Context - Nationality: {nationality}, Occupation: {occupation}, Annual Income: {annual_income}, "
        f"Marital Status: {marital_status}, Address: {current_address[:100]}, "
        f"Income Sources: {', '.join(sources_of_income) if sources_of_income else 'None'}\n\n"
        f"WebNotes: {web_prompt}\n\n"
    )

@pw.udf
def parse_raw_llm_text(to_parse: str) -> tuple[dict,str]:
    jsonfile, summary = extract_json_and_summary(to_parse)
    print("---- PARSED OUTPUT ----")
    print("JSON:")
    print(jsonfile)
    print("SUMMARY:")
    print(summary)

    jsonfile['summary'] = summary

    filename = "./out/results.jsonl"
    
    with open(filename, 'a', encoding='utf-8') as f:
        json.dump(jsonfile, f, indent=2)
    
    print(f"---- FILE SAVED ----")
    print(f"Saved to: {filename}")

    try:
        guard.validate(summary)
    except Exception as e:
        print(f"Guardrails validation failed on summary: {e}")
        summary = "LLM_ERROR: Guardrails validation failed on summary."
    
    if summary is None:
        summary = "No information found about the entity in any of the lists. Assume the entity to be neutral."
    return jsonfile, summary


@pw.udf
def generate_content(system_prompt: str, user_prompt: str) -> str:
    try:
        guard.validate(system_prompt)
        guard.validate(user_prompt)
    except Exception as e:
        print(f"Guardrails validation failed: {e}")
        return "LLM_ERROR: Guardrails validation failed."
    messages = pw.debug.table_from_rows(
        pw.schema_from_types(questions=list[dict]),
        rows=[
            (
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        ],
    )
    raw_responses = messages.select(raw_result=model(pw.this.questions))
    response = pw.debug.table_to_dicts(raw_responses)
    to_parse = str(list(response[1]['raw_result'].values())[0])
    print("---- LLM RAW RESPONSE ----")
    print(to_parse)
    return to_parse
