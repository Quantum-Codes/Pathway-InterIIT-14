import pathway as pw
from pathway import DateTimeNaive
from datetime import datetime, timedelta
import requests, os, psycopg2, sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.utils import get_current_naive_datetime

load_dotenv()
API_URL = "http://127.0.0.1:9000/score"

rdkafka_settings = {
    "bootstrap.servers": os.environ.get("BOOTSTRAP_SERVERS", "localhost:9092"),
    "group.id": os.environ.get("GROUP_ID", "0"),
    "session.timeout.ms": os.environ.get("SESSION_TIMEOUT_MS", "6000"),
    "auto.offset.reset": os.environ.get("AUTO_OFFSET_RESET", "earliest"),
}

connection_string_parts = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
    "dbname": os.environ.get("POSTGRES_DB", "values_db"),
    "user": os.environ.get("POSTGRES_USER", "user"),
    "password": os.environ.get("POSTGRES_PASSWORD", "password"),
}


conn = psycopg2.connect(
    host=connection_string_parts["host"],
    port=connection_string_parts["port"],
    dbname=connection_string_parts["dbname"],
    user=connection_string_parts["user"],
    password=connection_string_parts["password"],
)
cur = conn.cursor()

@pw.udf
def get_name(user_id: int) -> str:
    try:
        cur.execute("SELECT username FROM Users WHERE user_id = %s;", (user_id,))
        result = cur.fetchone()
        if result:
            return result[0]
        return "Unknown"
    except Exception:
        return "Unknown"

@pw.udf
def calculate_7d_ratio(user_id: int) -> float:
    """incoming_outgoing_ratio_7d = total incoming amount in last 7 days / total outgoing amount in last 7 days"""
    try:
        # Calculate outgoing (where user is the sender)
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0.0)
            FROM Transactions
            WHERE user_id = %s
              AND txn_timestamp >= NOW() - INTERVAL '7 days'
        """, (user_id,))
        outgoing = cur.fetchone()[0]
        
        # Calculate incoming (where user is the counterparty/receiver)
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0.0)
            FROM Transactions
            WHERE counterparty_id = %s
              AND txn_timestamp >= NOW() - INTERVAL '7 days'
        """, (user_id,))
        incoming = cur.fetchone()[0]
        
        # Calculate ratio (handle division by zero)
        if outgoing == 0:
            return 0.0 if incoming == 0 else 0.0
        return float(incoming) / float(outgoing)
    except Exception:
        return 0.0

@pw.udf
def normalize_ts(ts: str) -> DateTimeNaive:
    try:
        ts = ts.replace("Z", "")
        dt = datetime.fromisoformat(ts)
        return DateTimeNaive(dt)
    except Exception:
        return DateTimeNaive(datetime.utcnow())
    
@pw.udf
def nz(x):
    try:
        if x is None:
            return 0.0
        return float(x)
    except:
        return 0.0
    
@pw.udf
def to_int(x):
    try:
        if x is None:
            return 0
        return int(x)
    except:
        return 0
    
@pw.udf
def call_rps_api(feature_json: dict, user_id: int) -> float:
    try:
        response = requests.post(API_URL, json={"features": feature_json}, timeout=5)
        if response.status_code == 200:

            cur.execute("UPDATE Users SET rps_360 = %s, last_rps_calculation = NOW() WHERE user_id = %s;", (float(response.json().get("rps", 0.0)), user_id))
            conn.commit()
            return float(response.json().get("rps", 0.0))
        return 0.0
    except Exception:
        return 0.0
    
class InputSchema(pw.Schema):
    transaction_id: str
    user_id: int
    txn_timestamp: str
    amount: float
    currency: str
    txn_type: str
    counterparty_id: str
    is_fraud: int


trx = pw.io.debezium.read(
    rdkafka_settings,
    topic_name="postgres.public.transactions",
    schema=InputSchema,
    autocommit_duration_ms=100,
)


trx = trx.with_columns(
    ts=normalize_ts(trx.txn_timestamp)
)

GROUP = trx.groupby(trx.user_id)

# Pathway's ColumnReference objects don't expose per-window helper methods
# (like sum_in_window) in some versions. Compute per-window aggregates by
# creating separate windowed reductions (one per duration) and then joining
# the results together. We use sliding windows here so each reduction
# reflects the aggregation over the requested lookback period.

feats_1h = trx.windowby(
    trx.ts, 
    window=pw.temporal.sliding(duration=timedelta(hours=1), hop=timedelta(hours=1))
).reduce(
    user_ids=pw.reducers.any(pw.this.user_id),
    total_amount_1h=pw.reducers.sum(pw.this.amount),
    txn_count_1h=pw.reducers.count(pw.this.amount),
    unique_cp_1h=pw.reducers.any(pw.this.counterparty_id),
    max_amount_1h=pw.reducers.max(pw.this.amount),
    min_amount_1h=pw.reducers.min(pw.this.amount),
    avg_amount_1h=pw.reducers.avg(pw.this.amount),
)

feats_24h = trx.windowby(
    trx.ts, 
    window=pw.temporal.sliding(duration=timedelta(hours=24), hop=timedelta(hours=24))
).reduce(
    user_ids=pw.reducers.any(pw.this.user_id),
    total_amount_24h=pw.reducers.sum(pw.this.amount),
    txn_count_24h=pw.reducers.count(pw.this.amount),
    unique_cp_24h=pw.reducers.any(pw.this.counterparty_id),
    max_amount_24h=pw.reducers.max(pw.this.amount),
    min_amount_24h=pw.reducers.min(pw.this.amount),
    avg_amount_24h=pw.reducers.avg(pw.this.amount),
)

feats_7d = trx.windowby(
    trx.ts, 
    window=pw.temporal.sliding(duration=timedelta(days=7), hop=timedelta(days=7))
).reduce(
    user_ids=pw.reducers.any(pw.this.user_id),
    total_amount_7d=pw.reducers.sum(pw.this.amount),
    txn_count_7d=pw.reducers.count(pw.this.amount),
    unique_cp_7d=pw.reducers.any(pw.this.counterparty_id),
    max_amount_7d=pw.reducers.max(pw.this.amount),
    min_amount_7d=pw.reducers.min(pw.this.amount),
    avg_amount_7d=pw.reducers.avg(pw.this.amount),
)

feats_30d = trx.windowby(
    trx.ts, 
    window=pw.temporal.sliding(duration=timedelta(days=30), hop=timedelta(days=30))
).reduce(
    user_ids=pw.reducers.any(pw.this.user_id),
    total_amount_30d=pw.reducers.sum(pw.this.amount),
    txn_count_30d=pw.reducers.count(pw.this.amount),
    unique_cp_30d=pw.reducers.any(pw.this.counterparty_id),
    max_amount_30d=pw.reducers.max(pw.this.amount),
    min_amount_30d=pw.reducers.min(pw.this.amount),
    avg_amount_30d=pw.reducers.avg(pw.this.amount),
)

# Join all tables
joined = feats_1h.join(feats_24h, feats_1h.user_ids == feats_24h.user_ids) \
                .join(feats_7d, feats_1h.user_ids == feats_7d.user_ids) \
                .join(feats_30d, feats_1h.user_ids == feats_30d.user_ids)

# Select specific columns you need
feats = joined.select(
    # feats_1h columns
    pw.this.total_amount_1h,
    pw.this.txn_count_1h,
    pw.this.unique_cp_1h,
    pw.this.max_amount_1h,
    pw.this.min_amount_1h,
    pw.this.avg_amount_1h,
    # feats_24h columns (assuming similar naming)
    pw.this.total_amount_24h,
    pw.this.txn_count_24h,
    pw.this.unique_cp_24h,
    pw.this.max_amount_24h,
    pw.this.min_amount_24h,
    pw.this.avg_amount_24h,
    # feats_7d columns
    pw.this.total_amount_7d,
    pw.this.txn_count_7d,
    pw.this.unique_cp_7d,
    pw.this.max_amount_7d,
    pw.this.min_amount_7d,
    pw.this.avg_amount_7d,
    # feats_30d columns
    pw.this.total_amount_30d,
    pw.this.txn_count_30d,
    pw.this.unique_cp_30d,
    pw.this.max_amount_30d,
    pw.this.min_amount_30d,
    pw.this.avg_amount_30d,

    user_id = pw.this.user_ids,
    full_name = get_name(pw.this.user_ids),
    incoming_outgoing_ratio_7d = calculate_7d_ratio(pw.this.user_ids)
)

# Define which columns need nz() treatment
numeric_columns = [
    "total_amount_1h",
    "max_amount_1h", "min_amount_1h", "avg_amount_1h",
    "total_amount_24h",
    "max_amount_24h", "min_amount_24h", "avg_amount_24h",
    "total_amount_7d",
    "max_amount_7d", "min_amount_7d", "avg_amount_7d",
    "total_amount_30d",
    "max_amount_30d", "min_amount_30d", "avg_amount_30d",
]

int_columns = [
    "txn_count_1h", "unique_cp_1h",
    "txn_count_24h", "unique_cp_24h",
    "txn_count_7d", "unique_cp_7d",
    "txn_count_30d", "unique_cp_30d",
]

feats = feats.with_columns(
    **{col: nz(feats[col]) for col in numeric_columns}
)

feats = feats.with_columns(
    **{col: to_int(feats[col]) for col in int_columns}
)


@pw.udf
def as_dict(**kwargs):
    return kwargs

feats = feats.with_columns(
    feat_json=as_dict(**{col: nz(feats[col]) for col in numeric_columns})
)


feats = feats.with_columns(
    rps_score=call_rps_api(feats.feat_json, feats.user_id)
)

# processed_data = feats.select(
#     user_id=feats.user_ids,
#     rps_360=feats.rps_score,
#     rps_not = 0.0,
#     sanction_score = 0.0,
#     news_score = 0.0,
#     transaction_score = 0.0,
#     portfolio_score = 0.0,
#     calculated_at = get_current_naive_datetime(pw.this.user_ids), # ignored pw.this here
#     calculation_trigger = "transaction_update",
# )

pw.io.kafka.write(
    feats,
    rdkafka_settings,
    topic_name="rps_processed_features",
    format="json",
)

# Compute and print the table
pw.run(monitoring_level=pw.MonitoringLevel.NONE)
