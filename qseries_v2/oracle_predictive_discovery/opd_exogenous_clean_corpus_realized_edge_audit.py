
from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
RESULT=ROOT/"runtime"/"predictive_data"/"opd_exogenous_clean_corpus_realized_edge_audit_v2.json"

HURDLE=0.02
MIN_SEGMENT_N=12
MIN_UNIQUE_TICKERS=3

BTC_ALLOWED={
"source.crypto.condition.btc.bitcoin.fastest_fee_rate",
"source.crypto.condition.btc.bitcoin.half_hour_fee_rate",
"source.crypto.condition.btc.bitcoin.mempool_transaction_count",
"source.crypto.condition.btc.bitcoin.mempool_vsize",
"source.crypto.condition.btc.bitcoin.tip_block_size",
"source.crypto.condition.btc.bitcoin.tip_block_tx_count",
"source.crypto.condition.btc.bitcoin.tip_block_weight",
}

def load_jsonl(path):
    out=[]
    if not path.exists(): return out
    for line in path.read_text(encoding="utf-8").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def f(x):
    try:return float(x)
    except:return None

def clean_btc_row(r):
    if str(r.get("asset") or "").upper()!="BTC": return False
    snap=r.get("exogenous_evidence_snapshot")
    if not isinstance(snap,dict) or not snap: return False
    sids={str(v.get("source_id") or "") for v in snap.values() if isinstance(v,dict)}
    return bool(sids) and sids.issubset(BTC_ALLOWED)

def outcome_map(rows):
    return {str(r.get("prediction_id")):r for r in rows if r.get("prediction_id")}

def realized_return(o):
    for k in ("future_return","realized_return","directional_return"):
        v=f(o.get(k))
        if v is not None:return v
    return None

def signed_net(direction,r):
    if r is None:return None
    d=str(direction or "").upper()
    if d=="UP":gross=r
    elif d=="DOWN":gross=-r
    else:return None
    return gross-HURDLE

def mean(xs): return sum(xs)/len(xs) if xs else None

def lb95(xs):
    if not xs:return None
    if len(xs)==1:return xs[0]
    mu=mean(xs); sd=statistics.stdev(xs); se=sd/math.sqrt(len(xs))
    return mu-1.96*se

pred=load_jsonl(PRED)
outs=outcome_map(load_jsonl(OUTCOME))

clean=[r for r in pred if clean_btc_row(r)]
joined=[]
for p in clean:
    o=outs.get(str(p.get("prediction_id") or ""))
    if not o: continue
    rr=realized_return(o)
    net=signed_net(p.get("direction"),rr)
    if net is None: continue
    joined.append({
        "prediction_id":p.get("prediction_id"),
        "ticker":p.get("ticker"),
        "horizon_seconds":int(p.get("horizon_seconds") or 0),
        "direction":p.get("direction"),
        "realized_return":rr,
        "realized_net_after_2pct":net,
        "source_ids":sorted({str(v.get("source_id") or "") for v in p["exogenous_evidence_snapshot"].values() if isinstance(v,dict)}),
    })

segments={}
for r in joined:
    for sid in r["source_ids"]:
        k=(sid,r["horizon_seconds"],r["direction"])
        segments.setdefault(k,[]).append(r)

summ=[]
for (sid,h,d),rows in segments.items():
    nets=[x["realized_net_after_2pct"] for x in rows]
    uts={str(x["ticker"]) for x in rows}
    lb=lb95(nets)
    supported=len(rows)>=MIN_SEGMENT_N and len(uts)>=MIN_UNIQUE_TICKERS
    profitable=supported and lb is not None and lb>0
    summ.append({
        "source_id":sid,"horizon_seconds":h,"direction":d,
        "n":len(rows),"unique_tickers":len(uts),
        "mean_net_after_2pct":mean(nets),
        "median_net_after_2pct":statistics.median(nets) if nets else None,
        "positive_net_rate":sum(1 for x in nets if x>0)/len(nets) if nets else None,
        "cumulative_net_after_2pct":sum(nets),
        "lower_bound_net_after_2pct":lb,
        "supported":supported,
        "profitable_supported":profitable,
    })

summ.sort(key=lambda x:(x["profitable_supported"],x["supported"],x["lower_bound_net_after_2pct"] if x["lower_bound_net_after_2pct"] is not None else -999),reverse=True)
wins=[x for x in summ if x["profitable_supported"]]

payload={
"revision":"EXOGENOUS_CLEAN_CORPUS_REALIZED_EDGE_AUDIT_V2",
"hurdle":HURDLE,
"clean_prediction_rows":len(clean),
"clean_resolved_rows":len(joined),
"segments":len(summ),
"supported_segments":sum(1 for x in summ if x["supported"]),
"profitable_supported_segments":len(wins),
"winners":wins[:50],
"top_segments":summ[:100],
}
RESULT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

print("[CLEAN BTC PREDICTION ROWS]",len(clean))
print("[CLEAN BTC RESOLVED ROWS]",len(joined))
print("[SEGMENTS]",len(summ))
print("[SUPPORTED SEGMENTS]",payload["supported_segments"])
print("[PROFITABLE SUPPORTED SEGMENTS]",len(wins))
for x in summ[:30]:
    print("[SEGMENT]",x["source_id"],"H=",x["horizon_seconds"],"DIR=",x["direction"],
          "N=",x["n"],"TICKERS=",x["unique_tickers"],
          "MEAN_NET=",x["mean_net_after_2pct"],
          "LB95=",x["lower_bound_net_after_2pct"],
          "POS_RATE=",x["positive_net_rate"],
          "PROFITABLE_SUPPORTED=",x["profitable_supported"])
print("[RESULT FILE]",RESULT)
if wins:
    print("[RESULT] CLEAN_EXOGENOUS_PROSPECTIVE_PROFITABLE_SEGMENT_FOUND")
else:
    print("[RESULT] NO_CLEAN_EXOGENOUS_PROSPECTIVE_PROFITABLE_SEGMENT_YET")
print("[MODEL MUTATION] FALSE")
print("[THRESHOLD/HURDLE CHANGE] FALSE/FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
