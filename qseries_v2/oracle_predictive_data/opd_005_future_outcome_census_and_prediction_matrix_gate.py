
from pathlib import Path
from bisect import bisect_right
from collections import defaultdict, Counter
import hashlib, json

HORIZONS=(30,60,300,900,3600)
MAX_ANCHORS_PER_TICKER=250

def _hash(x):
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()

def _price(row):
    if row.get("trade_price") is not None:
        return float(row["trade_price"])
    b=row.get("yes_bid"); a=row.get("yes_ask")
    if b is not None and a is not None:
        return (float(b)+float(a))/2.0
    return None

def build(root=None):
    root=Path(root or Path.cwd())
    src=root/"runtime"/"predictive_data"/"opd_004_kalshi_raw_state_at_t.json"
    state=json.loads(src.read_text(encoding="utf-8"))
    by=defaultdict(list)
    for r in state["rows"]:
        px=_price(r)
        if px is not None and 0.0<=px<=1.0:
            by[r["ticker"]].append((float(r["event_epoch"]),px,r))
    for t in by: by[t].sort(key=lambda x:x[0])

    outcomes=[]
    horizon_counts=Counter()
    for ticker,series in by.items():
        if len(series)<2: continue
        step=max(1,len(series)//MAX_ANCHORS_PER_TICKER)
        times=[x[0] for x in series]
        for i in range(0,len(series)-1,step):
            t0,p0,r0=series[i]
            for h in HORIZONS:
                end=t0+h
                j=bisect_right(times,end)-1
                if j<=i or times[-1]<end: continue
                future=series[i+1:j+1]
                if not future: continue
                pend=future[-1][1]
                mx=max(future,key=lambda x:x[1])
                mn=min(future,key=lambda x:x[1])
                mfe=mx[1]-p0
                mae=mn[1]-p0
                row={
                    "ticker":ticker,
                    "anchor_sequence_number":r0["sequence_number"],
                    "anchor_epoch":t0,
                    "anchor_price":p0,
                    "horizon_seconds":h,
                    "future_end_price":pend,
                    "future_return":pend-p0,
                    "mfe":mfe,
                    "mae":mae,
                    "time_to_max_seconds":mx[0]-t0,
                    "time_to_min_seconds":mn[0]-t0,
                    "hit_plus_05":mfe>=.05,
                    "hit_minus_05":mae<=-.05,
                    "hit_plus_10":mfe>=.10,
                    "hit_minus_10":mae<=-.10,
                    "label_strictly_future":True,
                }
                outcomes.append(row); horizon_counts[h]+=1

    outcomes.sort(key=lambda x:(x["anchor_epoch"],x["ticker"],x["horizon_seconds"]))
    matrix_ready = len(outcomes)>0 and len(horizon_counts)>=2
    payload={
        "schema_version":"OPD-005",
        "source_state_hash":state["state_hash"],
        "outcomes":outcomes,
        "outcome_rows":len(outcomes),
        "horizon_counts":dict(sorted(horizon_counts.items())),
        "ticker_count":len(set(x["ticker"] for x in outcomes)),
        "plus_05_count":sum(x["hit_plus_05"] for x in outcomes),
        "minus_05_count":sum(x["hit_minus_05"] for x in outcomes),
        "plus_10_count":sum(x["hit_plus_10"] for x in outcomes),
        "minus_10_count":sum(x["hit_minus_10"] for x in outcomes),
        "prediction_matrix_pavement_ready":matrix_ready,
        "next_required":"JOIN_EXTERNAL_AND_ORACLE_RAW_STATE_AT_OR_BEFORE_EACH_ANCHOR_T",
        "model_fit_allowed":False,
        "edge_proven":False,
        "probability_enabled":False,
        "direction_enabled":False,
        "publication_allowed":False,
        "execution_authority":False,
        "outcome_hash":_hash(outcomes),
    }
    p=root/"runtime"/"predictive_data"/"opd_005_future_outcome_census.json"
    p.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")
    return payload,p
