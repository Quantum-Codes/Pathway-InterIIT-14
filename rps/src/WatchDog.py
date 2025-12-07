import pathway as pw
from pathway import DateTimeNaive
from datetime import datetime, timedelta
import requests

INPUT_FILE = "./unified_modified.csv"
API_URL = "http://127.0.0.1:8000/score"

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
def call_rps_api(feature_json: dict) -> float:
    try:
        response = requests.post(API_URL, json={"features": feature_json}, timeout=5)
        if response.status_code == 200:
            return float(response.json().get("rps", 0.0))
        return 0.0
    except Exception:
        return 0.0
    
class InputSchema(pw.Schema):
    transaction_id: str
    user_id: str
    timestamp: str
    amount: float
    currency: str
    txn_type: str
    counterparty_id: str
    country: str | None
    device_id: str | None
    is_fraud: int

def main():
    print("Watching CSV:", INPUT_FILE)

    
    trx = pw.io.csv.read(
        INPUT_FILE,
        mode="streaming",
        schema=InputSchema,
    )

    
    trx = trx.with_columns(
        ts=normalize_ts(trx.timestamp)
    )

    
    # GROUP = trx.groupby(trx.user_id)

    # feats = GROUP.windowby(trx.ts, window=pw.temporal.session(max_gap=timedelta(hours=1))).reduce(
    #     user_id=trx.user_id,
    #     total_amount_1h=trx.amount.sum_in_window(pw.duration(hours=1)),
    #     txn_count_1h=trx.amount.count_in_window(pw.duration(hours=1)),
    #     unique_cp_1h=trx.counterparty_id.nunique_in_window(pw.duration(hours=1)),
    #     max_amount_1h=trx.amount.max_in_window(pw.duration(hours=1)),
    #     min_amount_1h=trx.amount.min_in_window(pw.duration(hours=1)),
    #     avg_amount_1h=trx.amount.avg_in_window(pw.duration(hours=1)),

        
    #     total_amount_24h=trx.amount.sum_in_window(pw.duration(hours=24)),
    #     txn_count_24h=trx.amount.count_in_window(pw.duration(hours=24)),
    #     unique_cp_24h=trx.counterparty_id.nunique_in_window(pw.duration(hours=24)),
    #     max_amount_24h=trx.amount.max_in_window(pw.duration(hours=24)),
    #     min_amount_24h=trx.amount.min_in_window(pw.duration(hours=24)),
    #     avg_amount_24h=trx.amount.avg_in_window(pw.duration(hours=24)),

        
    #     total_amount_7d=trx.amount.sum_in_window(pw.duration(days=7)),
    #     txn_count_7d=trx.amount.count_in_window(pw.duration(days=7)),
    #     unique_cp_7d=trx.counterparty_id.nunique_in_window(pw.duration(days=7)),
    #     max_amount_7d=trx.amount.max_in_window(pw.duration(days=7)),
    #     min_amount_7d=trx.amount.min_in_window(pw.duration(days=7)),
    #     avg_amount_7d=trx.amount.avg_in_window(pw.duration(days=7)),

        
    #     total_amount_30d=trx.amount.sum_in_window(pw.duration(days=30)),
    #     txn_count_30d=trx.amount.count_in_window(pw.duration(days=30)),
    #     unique_cp_30d=trx.counterparty_id.nunique_in_window(pw.duration(days=30)),
    #     max_amount_30d=trx.amount.max_in_window(pw.duration(days=30)),
    #     min_amount_30d=trx.amount.min_in_window(pw.duration(days=30)),
    #     avg_amount_30d=trx.amount.avg_in_window(pw.duration(days=30)),
    # )

    GROUP = trx.groupby(trx.user_id)

    # Pathway's ColumnReference objects don't expose per-window helper methods
    # (like sum_in_window) in some versions. Compute per-window aggregates by
    # creating separate windowed reductions (one per duration) and then joining
    # the results together. We use sliding windows here so each reduction
    # reflects the aggregation over the requested lookback period.

    # feats_1h = GROUP.windowby(trx.ts, window=pw.temporal.sliding(duration=timedelta(hours=1), hop=timedelta(hours=3))).reduce(
    #     user_id=trx.user_id,
    #     total_amount_1h=pw.reducers.sum(trx.amount),
    #     txn_count_1h=pw.reducers.count(trx.amount),
    #     unique_cp_1h=pw.reducers.unique(trx.counterparty_id),
    #     max_amount_1h=pw.reducers.max(trx.amount),
    #     min_amount_1h=pw.reducers.min(trx.amount),
    #     avg_amount_1h=pw.reducers.avg(trx.amount),
    # )

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

    # Group by user first, then apply time window
    # feats_1h = trx.groupby(trx.user_id).windowby(
    #     trx.ts, 
    #     window=pw.temporal.sliding(duration=timedelta(hours=1), hop=timedelta(hours=3))
    # ).reduce(
    #     pw.this.user_id,  # Already in groupby
    #     total_amount_1h=pw.reducers.sum(trx.amount),
    #     txn_count_1h=pw.reducers.count(trx.amount),
    #     unique_cp_1h=pw.reducers.unique(trx.counterparty_id),
    #     max_amount_1h=pw.reducers.max(trx.amount),
    #     min_amount_1h=pw.reducers.min(trx.amount),
    #     avg_amount_1h=pw.reducers.avg(trx.amount),
    # )

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

    # Join the separate windowed feature tables on user_id. If your Pathway
    # version uses a different join signature adjust the call accordingly.
    # feats = feats_1h.join(feats_24h, on="user_id").join(feats_7d, on="user_id").join(feats_30d, on="user_id")

    # Join all tables
    joined = feats_1h.join(feats_24h, feats_1h.user_ids == feats_24h.user_ids) \
                    .join(feats_7d, feats_1h.user_ids == feats_7d.user_ids) \
                    .join(feats_30d, feats_1h.user_ids == feats_30d.user_ids)

    # Select specific columns you need
    feats = joined.select(
        pw.this.user_ids,
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
        # feats_7d columns
        pw.this.total_amount_7d,
        pw.this.txn_count_7d,
        # feats_30d columns
        pw.this.total_amount_30d,
        pw.this.txn_count_30d,
    )
    
    # feats = feats.with_columns(
    #     **{col: nz(feats[col]) for col in feats.columns if col not in ["user_id"]}
    # )

    # Define which columns need nz() treatment
    numeric_columns = [
        "total_amount_1h", "txn_count_1h", "unique_cp_1h", 
        "max_amount_1h", "min_amount_1h", "avg_amount_1h",
        "total_amount_24h", "txn_count_24h",
        "total_amount_7d", "txn_count_7d",
        "total_amount_30d", "txn_count_30d"
    ]

    feats = feats.with_columns(
        **{col: nz(feats[col]) for col in numeric_columns}
    )

    
    @pw.udf
    def as_dict(**kwargs):
        return kwargs

    feats = feats.with_columns(
        feat_json=as_dict(**{col: nz(feats[col]) for col in numeric_columns})
    )

    
    feats = feats.with_columns(
        rps_score=call_rps_api(feats.feat_json)
    )
    
    # Compute and print the table
    pw.debug.compute_and_print(feats)
    pw.run()

if __name__ == "__main__":
    main()