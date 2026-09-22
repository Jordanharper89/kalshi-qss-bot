
from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
RESULT=ROOT/"runtime"/"predictive_data"/"opd_exogenous_prospective_realized_edge_audit_v1.json"

HURDLE=0.02
MIN_SEGMENT_N=12
MIN_UNIQUE_TICKERS=3

DENY=("prospective_forecast","prospective_binding","experience","source.sports","sports.",
      "kalshi","coinbase","polymarket","learned_case")

def load_jsonl(path):
    out=[]
    if not path.exists(): return out
    for line in path.read_text(encoding="utf-8").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def safe_float(x):
    try: return float(x)
    except Exception: return None

def clean_snapshot(row):
    x=row.get("exogenous_evidence_snapshot")
    if not isinstance(x,dict) or not x: return {}
    out={}
    for k,v in x.items():
        if not isinstance(v,dict): continue
        sid=str(v.get("source_id") or "")
        typ=str(v.get("observation_type") or "")
        low=(sid+" "+typ).lower()
        if any(z in low for z in DENY): continue
        out[k]=v
    return out

def outcome_map(rows):
    m={}
    for r in rows:
        pid=str(r.get("prediction_id") or "")
        if not pid: continue
        # Prefer exact-future resolved rows only.
        status=str(r.get("status") or r.get("resolution_status") or "").upper()
        if status and "RESOLV" not in status and "EXACT" not in status:
            pass
        m[pid]=r
    return m

def realized_return(o):
    for k in ("future_return","realized_return","directional_return"):
        v=safe_float(o.get(k))
        if v is not None: return v
    return None

def mfe(o):
    for k in ("mfe","future_mfe","max_favorable_excursion"):
        v=safe_float(o.get(k))
        if v is not None: return v
    return None

def mae(o):
    for k in ("mae","future_mae","max_adverse_excursion"):
        v=safe_float(o.get(k))
        if v is not None: return v
    return None

def signed_net(direction,r):
    if r is None: return None
    d=str(direction or "").upper()
    if d=="UP": gross=r
    elif d=="DOWN": gross=-r
    else: return None
    return gross-HURDLE

def mean(xs):
    return sum(xs)/len(xs) if xs else None

def stdev(xs):
    return statistics.stdev(xs) if len(xs)>=2 else 0.0 if len(xs)==1 else None

def lower_bound(xs):
    if len(xs)<2: return mean(xs)
    mu=mean(xs); sd=stdev(xs); se=sd/math.sqrt(len(xs))
    return mu-1.96*se

pred=load_jsonl(PRED)
outcomes=outcome_map(load_jsonl(OUTCOME))

joined=[]
for p in pred:
    snap=clean_snapshot(p)
    if not snap: continue
    pid=str(p.get("prediction_id") or "")
    o=outcomes.get(pid)
    if not o: continue
    rr=realized_return(o)
    net=signed_net(p.get("direction"),rr)
    if net is None: continue
    joined.append({
        "prediction_id":pid,
        "ticker":p.get("ticker"),
        "asset":p.get("asset"),
        "horizon_seconds":int(p.get("horizon_seconds") or 0),
        "direction":p.get("direction"),
        "predicted_probability":safe_float(p.get("predicted_probability")),
        "expected_return":safe_float(p.get("expected_return")),
        "realized_return":rr,
        "realized_net_after_2pct":net,
        "mfe":mfe(o),
        "mae":mae(o),
        "source_ids":sorted({str(v.get("source_id") or "") for v in snap.values()}),
        "snapshot":snap,
    })

segments={}
for r in joined:
    h=r["horizon_seconds"]
    for sid in r["source_ids"]:
        k=(sid,h,r["direction"])
        segments.setdefault(k,[]).append(r)

summaries=[]
for (sid,h,direction),rows in segments.items():
    nets=[x["realized_net_after_2pct"] for x in rows]
    tickers={str(x["ticker"]) for x in rows}
    hit=sum(1 for x in nets if x>0)/len(nets)
    lb=lower_bound(nets)
    summaries.append({
        "source_id":sid,
        "horizon_seconds":h,
        "direction":direction,
        "n":len(rows),
        "unique_tickers":len(tickers),
        "mean_net_after_2pct":mean(nets),
        "median_net_after_2pct":statistics.median(nets) if nets else None,
        "positive_net_rate":hit,
        "cumulative_net_after_2pct":sum(nets),
        "lower_bound_net_after_2pct":lb,
        "supported":len(rows)>=MIN_SEGMENT_N and len(tickers)>=MIN_UNIQUE_TICKERS,
        "profitable_supported":len(rows)>=MIN_SEGMENT_N and len(tickers)>=MIN_UNIQUE_TICKERS and lb is not None and lb>0,
    })

summaries.sort(key=lambda x:(x["profitable_supported"],x["supported"],x["lower_bound_net_after_2pct"] if x["lower_bound_net_after_2pct"] is not None else -999),reverse=True)
winners=[x for x in summaries if x["profitable_supported"]]

payload={
    "revision":"EXOGENOUS_PROSPECTIVE_REALIZED_EDGE_AUDIT_V1",
    "hurdle":HURDLE,
    "min_segment_n":MIN_SEGMENT_N,
    "min_unique_tickers":MIN_UNIQUE_TICKERS,
    "clean_resolved_rows":len(joined),
    "segments":len(summaries),
    "supported_segments":sum(1 for x in summaries if x["supported"]),
    "profitable_supported_segments":len(winners),
    "winners":winners[:50],
    "top_segments":summaries[:100],
}
RESULT.parent.mkdir(parents=True,exist_ok=True)
RESULT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

print("[CLEAN RESOLVED EXOGENOUS ROWS]",len(joined))
print("[SEGMENTS]",len(summaries))
print("[SUPPORTED SEGMENTS]",payload["supported_segments"])
print("[PROFITABLE SUPPORTED SEGMENTS]",len(winners))
for x in summaries[:20]:
    print("[SEGMENT]",x["source_id"],"H=",x["horizon_seconds"],"DIR=",x["direction"],
          "N=",x["n"],"TICKERS=",x["unique_tickers"],
          "MEAN_NET=",x["mean_net_after_2pct"],
          "LB95=",x["lower_bound_net_after_2pct"],
          "POS_RATE=",x["positive_net_rate"],
          "SUPPORTED=",x["supported"],
          "PROFITABLE_SUPPORTED=",x["profitable_supported"])
print("[RESULT FILE]",RESULT)
if winners:
    print("[RESULT] EXOGENOUS_PROSPECTIVE_PROFITABLE_SEGMENT_FOUND")
else:
    print("[RESULT] NO_EXOGENOUS_PROSPECTIVE_PROFITABLE_SEGMENT_YET")
print("[MODEL MUTATION] FALSE")
print("[THRESHOLD/HURDLE CHANGE] FALSE/FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
