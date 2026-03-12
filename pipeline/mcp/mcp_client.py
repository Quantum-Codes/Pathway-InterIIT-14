import os, sys, uuid
import shutil, json
from pathlib import Path
import pathway as pw
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from post_aggregator import update_rps_based_on_conditions

import crewai.mcp.client as mcp_client_mod

mcp_client_mod.MCP_TOOL_EXECUTION_TIMEOUT = 300

from crewai.mcp.client import MCPClient as _MCPClient
_orig_init = _MCPClient.__init__

def _patched_init(self, *args, **kwargs):
    kwargs["execution_timeout"] = 300    # hard override
    return _orig_init(self, *args, **kwargs)
_MCPClient.__init__ = _patched_init

from crewai.mcp import MCPServerHTTP
from crewai import Agent

load_dotenv()
PATHWAY_MCP_URL = os.environ.get("PATHWAY_MCP_URL", "http://localhost:8123/mcp/")
INBOX_DIR = Path("inbox").resolve()
FRAUD_TOPIC = os.environ.get("FRAUD_TOPIC", "possible_fraud")

os.environ["GOOGLE_API_KEY"] = os.environ["ALT_GOOGLE_API_KEY"]

rdkafka_settings = {
    "bootstrap.servers": os.environ.get("BOOTSTRAP_SERVERS", "localhost:9092"),
    "group.id": os.environ.get("GROUP_ID", "0"),
    "session.timeout.ms": os.environ.get("SESSION_TIMEOUT_MS", "6000"),
    "auto.offset.reset": os.environ.get("AUTO_OFFSET_RESET", "earliest"),
}

connection_string_parts = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
    "dbname": os.environ.get("POSTGRES_DBNAME", "values_db"),
    "user": os.environ.get("POSTGRES_USER", "user"),
    "password": os.environ["POSTGRES_PASSWORD"],
}

mcp_server = MCPServerHTTP(url=PATHWAY_MCP_URL, streamable=True,cache_tools_list=True)
agent = Agent(
    role="Analyst agent",
    llm="gemini-2.5-flash",
    goal="Decide which tools to call and get context for validation of score",
    backstory="Decide which tools to call and get context for validation of score",
    mcps=[mcp_server]
)

@pw.udf
def make_title(full_name: str) -> str:
    return f"Compliance Alert for {full_name}"

@pw.udf
def join_tags(tags: str) -> str:
    """its like this: "[\"anomaly\", \"single_high_value_transaction\", \"manual_review_recommended\"]" """
    try:
        tag_list = json.loads(tags)
        return ", ".join(tag_list)
    except Exception:
        return tags

@pw.udf
def make_uuid(user_id: int) -> str:
    # make a uuid from user_id
    return str(uuid.uuid4())

@pw.udf
def call_mcp_client(full_name, rps, risk_level, anomaly, p_ml, evidence, tags, short_reason, long_reason, recommended_action):
    # Use kickoff() to interact directly with the agent
    result = agent.kickoff(
        f"""
You are an expert Financial Crime Risk Analyst. 
Your goal is to validate the 'rps' for the transaction below.

### TRANSACTION METADATA
- *Entity (name)*: {full_name}
- *Risk Level*: {risk_level}
- *Scores*: Anomaly={anomaly:.2f}, RPS={rps:.2f}, P_ML={p_ml:.2f}, Evidence={evidence:.4f}
- *Tags*: {tags}

### ANALYSIS CONTEXT
*Short Summary*: {short_reason}
*Detailed Analysis*: {long_reason}
*System Recommendation*: {recommended_action}

### YOUR TASK
Analyze the provided metadata and reasoning. You have access to three validation tools:
1. ofac_call: Checks for global sanctions.
2. pep_call: Checks for Politically Exposed Person status.

*Decide the following:*
Does the combination of the anomaly score, the entity's identity, and the RPS justification require tool calls? 
- If YES: Call the necessary tool(s) to verify the specific risks you see.
- If NO: Return a validation based on the given evidence yourself, without calling any tools
"""
    )

    return result.raw

class EntitiesSchema(pw.Schema):
    name: str

class RPSSchema(pw.Schema):
    user_id: int
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

rps_output = pw.io.kafka.read(
    rdkafka_settings,
    topic=FRAUD_TOPIC,
    format="json",
    schema=RPSSchema,
    autocommit_duration_ms=100,
)

@pw.udf
def join_validations(short_reason, long_reason, recommended_action):
    return f"{short_reason}\n{long_reason}\nSystem Recommendation: {recommended_action}"

filtered = rps_output.filter(pw.this.rps > 0.4)

mcp_output = filtered.with_columns(
    name = pw.this.full_name,
    rps360 = pw.this.rps,
    rps0 = update_rps_based_on_conditions(pw.this.user_id, pw.this.rps),
)

try: 
    mcp_output = mcp_output.with_columns(
            mcp_output = call_mcp_client(
            full_name = pw.this.full_name, 
            rps = pw.this.rps,
            risk_level = pw.this.risk_level,
            anomaly = pw.this.anomaly,
            p_ml = pw.this.p_ml,
            evidence = pw.this.evidence,
            tags = pw.this.tags,
            short_reason = pw.this.short_reason,
            long_reason = pw.this.long_reason,
            recommended_action = pw.this.recommended_action,
        ),
    )
except Exception as e:
    # fallback to no mcp output
    mcp_output = mcp_output.with_columns(
        mcp_output = join_validations(pw.this.short_reason, pw.this.long_reason, pw.this.recommended_action),
    )
pw.io.csv.write(mcp_output, INBOX_DIR / "mcp_output.csv")

mcp_output = mcp_output.select(
    user_id = pw.this.user_id,
    alert_type = "transaction_alert",
    triggered_by = "transaction_monitoring_system",
    title = make_title(pw.this.full_name),
    severity = pw.this.risk_level,
    priority = pw.this.risk_level,
    rps360 = pw.this.rps360,
    description = pw.this.mcp_output,
    entity_id = make_uuid(pw.this.user_id),
    alert_metadata = join_tags(pw.this.tags)
)

pw.io.postgres.write(
        mcp_output,
        connection_string_parts,
        table_name="compliance_alerts",
)

def clean_persistent_storage():
    if os.path.exists("./mcp/MCPState"):
        shutil.rmtree("./mcp/MCPState")

if __name__ == "__main__":
    #clean_persistent_storage()

    backend = pw.persistence.Backend.filesystem("./mcp/MCPState")
    persistence_config = pw.persistence.Config(backend)
    
    pw.run(
        monitoring_level=pw.MonitoringLevel.NONE, # no MonitoringMode / autocommit args in your version
        persistence_config=persistence_config, # Change: persistence config passed to the method
    )
