import asyncio, os, jsonlines
import shutil
from pathlib import Path
import pathway as pw

import crewai.mcp.client as mcp_client_mod

mcp_client_mod.MCP_TOOL_EXECUTION_TIMEOUT = 300

from crewai.mcp.client import MCPClient as _MCPClient
_orig_init = _MCPClient.__init__

def _patched_init(self, *args, **kwargs):
    kwargs["execution_timeout"] = 300    # hard override
    # kwargs.setdefault("connect_timeout", 60)
    # kwargs.setdefault("discovery_timeout", 60)
    return _orig_init(self, *args, **kwargs)
_MCPClient.__init__ = _patched_init

from crewai.mcp import MCPServerHTTP
from crewai import Agent

PATHWAY_MCP_URL = "http://localhost:8123/mcp/"

os.environ["GOOGLE_API_KEY"] = "AIzaSyA3fB0G8XyjVXgVxCH7BK9uaSJHx5kpMGg"

def _abs_glob(glob_str: str) -> str:
    p = Path(os.path.expanduser(glob_str))
    parent = p.parent.resolve()
    return str(parent / p.name)

INBOX_GLOB = _abs_glob(os.getenv("INBOX_GLOB", "inbox/names_to_check.csv"))

@pw.udf
def call_mcp_client(name):
    mcp_server = MCPServerHTTP(url=PATHWAY_MCP_URL, streamable=True,cache_tools_list=True)

    agent = Agent(
        role="Analyst agent",
        llm="gemini-2.5-flash",
        goal="Decide which tools to call and get context for validation of score",
        backstory="Decide which tools to call and get context for validation of score",
        mcps=[mcp_server]
    )
    # Use kickoff() to interact directly with the agent
        
    result = agent.kickoff(f"Given rho_360 = 0.5 and explanation = '{name} has political exposure and bad news'. This guy: " + name)
    # print(result.raw)
    # with jsonlines.open('mcp_output.jsonl', mode='a') as writer:
    # Access the raw response
        # writer.write(result.raw)
    # print(result.raw)

    return result.raw

class EntitiesSchema(pw.Schema):
    name: str

class RPSSchema(pw.Schema):
    user_id: str
    full_name: str
    p_ml: float
    anomaly: float
    evidence: float
    rps: float
    risk_level: str
    short_reason: str
    long_reason: str
    recommended_action: str
    tags: str

# entities = pw.io.csv.read(
#     path="/home/hades/Pathway/streaming-20251111T181915Z-1-001/streaming/inbox/names_to_check.csv",
#     schema=EntitiesSchema,
#     mode="streaming",
# )

rps_output = pw.io.jsonlines.read(
    "/home/hades/Pathway/streaming-20251111T181915Z-1-001/streaming/inbox/rps_output.jsonl", 
    schema=RPSSchema, 
    mode="streaming"
)

filtered = rps_output.filter(pw.this.rps > 0.4)

mcp_output = filtered.select(
    name = pw.this.full_name,
    rps360 = pw.this.rps,
    mcp_output = call_mcp_client(pw.this.full_name),
)

pw.io.csv.write(mcp_output, "/home/hades/Pathway/streaming-20251111T181915Z-1-001/streaming/inbox/mcp_output.csv")

def clean_persistent_storage():
    if os.path.exists("./MCPPState"):
        shutil.rmtree("./MCPPState")

if __name__ == "__main__":
    clean_persistent_storage()

    backend = pw.persistence.Backend.filesystem("./MCPPState")
    persistence_config = pw.persistence.Config(backend)
    
    pw.run(
        monitoring_level=pw.MonitoringLevel.NONE, # no MonitoringMode / autocommit args in your version
        persistence_config=persistence_config, # Change: persistence config passed to the method
    )
