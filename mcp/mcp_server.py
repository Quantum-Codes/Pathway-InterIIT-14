import time
import pathway as pw
from pathway.xpacks.llm.mcp_server import McpServable, McpServer, PathwayMcp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llm_output import run_web_analysis

pw.set_license_key("4592EB-AEC4F8-38452F-235989-C3910E-V3")

"""
CONVERTED OFAC CONNECTOR -> OFAC API CALL FUNCTION
"""

import requests, os, json
import pathway as pw
from pathway.io.python import ConnectorSubject

@pw.udf(return_type=dict, deterministic=False)
def pep_screen(qname: str) -> dict:
    OS_API_KEY="50fb68336ac9a4f12a79699431fb41df"    
    OS_URL = "https://api.opensanctions.org/match/default"

    _http = requests.Session()

    headers = {"Authorization": OS_API_KEY}
    payload = {"queries": {"q": {"schema": "Person", "properties": {"name": [qname]}}}}
    r = _http.post(OS_URL, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    res = r.json().get("responses", {}).get("q", {}).get("results", []) or []
    if not res:
        return {"entity_id": None, "entity_name": None, "score": None, "data": None}
    m = res[0]
    ent = (m.get("entity") or {})
    props = (ent.get("properties") or {})
    names = props.get("name") or []
    return {
        "entity_id": ent.get("id"),
        "entity_name": names[0] if names else None,
        "score": m.get("score"),
        "data": m,
    }

@pw.udf(return_type=dict, deterministic=False)
def ofac_screen(name: str):
    BASE_URL = "https://api.ofac-api.com/v4"
    API_KEY = "824a2c8c-7d08-4e9f-9c27-2195651f57bf"
    cases = [{"name": name}]
    resp = requests.post(
        f"{BASE_URL}/screen",
        json={"apiKey": API_KEY, "cases": cases},
    )
    resp.raise_for_status()
    
    records = []
    for record in resp.json().get("results", []):
        for match in record.get("matches", []):
            records.append({
                "query_name": record.get("name"),
                "entity_id": match.get("sanction", {}).get("id"),
                "entity_name": match.get("sanction", {}).get("name"),
                "score": match.get("score"),
                "data": match,
            })
    return records


class OFACSchema(pw.Schema):
    query_name: str = pw.column_definition(primary_key=True)
    entity_id: str | None
    entity_name: str | None
    score: float | None
    data: dict | None


# 1. Define the input schema for the tool request.
class DecisionRequestSchema(pw.Schema):
    score: float        # numeric score input
    explanation: str    # string explanation input
    name: str

# 2. Define the tool class that selects APIs based on input.
class ApiSelector(McpServable):
    def ofac_call(self, input_table: pw.Table) -> pw.Table:
        """get random number"""
        return input_table.select(result=ofac_screen(input_table.name))
    
    def pep_call(self, input_table: pw.Table) -> pw.Table:
        """Check if `name: str` is a Politically Exposed Person."""
        return input_table.select(result = pep_screen(input_table.name))
    
    def news_call(self, input_table: pw.Table) -> pw.Table:
        """Search adverse media about `name:str`"""
        return input_table.select(result = run_web_analysis(input_table.name))
    
    def register_mcp(self, server: McpServer):
        # Register the tool with the MCP server under name "ofac_call".
        server.tool(
            "ofac_call",
            request_handler=self.ofac_call,
            schema=DecisionRequestSchema
        )
        server.tool(
            "pep_call",
            request_handler=self.pep_call,
            schema=DecisionRequestSchema
        )
        server.tool(
            "news_call",
            request_handler=self.news_call,
            schema=DecisionRequestSchema
        )

# 3. Instantiate the tool and MCP server configuration.
selector_tool = ApiSelector()
pathway_mcp_server = PathwayMcp(
    name="API-Selector-MCP",
    transport="streamable-http",   # HTTP transport for MCP
    host="localhost",
    port=8123,
    serve=[selector_tool]
)

if __name__ == "__main__":
    # 4. Run the Pathway engine to start the MCP server.
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)
