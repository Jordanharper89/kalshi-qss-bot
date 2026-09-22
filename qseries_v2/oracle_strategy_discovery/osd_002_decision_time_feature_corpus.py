from pathlib import Path
import json,math,bisect
from collections import defaultdict
ROOT=Path.cwd().resolve()
PRED=ROOT/"runtime/predictive_data/opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME=ROOT/"runtime/predictive_data/opd_full_evidence_live_outcome_ledger.jsonl"
MICRO=ROOT/"runtime/strategy_discovery/osd_001_kalshi_microstructure_archive.jsonl"
COINBASE=ROOT/"runtime/coinbase_hf/historical_condition_windows.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_002_strategy_feature_corpus.jsonl"
WINDOWS=(5,15,30,60,300)

def loadj(path):
    a=[]
    if not path.exists(): return a
    for line in path.open(encoding="utf-8"):
        try:a.append(json.loads(line))
        except:pass
    return a

def first(d,names):
    for k in names:
        if d.get(k) is not None:return d.get(k)
    return None

def epoch(d):
    v=first(d,("prediction_epoch","frozen_epoch","created_epoch","anchor_epoch","observed_epoch"))
    try:return float(v)
    except:return None

def pid(d):
    v=first(d,("prediction_id","prediction_record_id","prospective_prediction_id","state_id"))
    return str(v) if v is not None else ""

def ticker(d): return str(first(d,("ticker","market_ticker","kalshi_ticker")) or "")
def horizon(d):
    try:return int(first(d,("horizon_seconds","horizon","forecast_horizon_seconds")))
    except:return None

def future_ret(d):
    for k in ("future_return","realized_return","yes_price_return","price_return","return"):
        try:
            if d.get(k) is not None:return float(d[k])
        except:pass
    return None

preds=loadj(PRED); outs=loadj(OUTCOME); micro=loadj(MICRO)
pby={pid(x):x for x in preds if pid(x)}
oby={pid(x):x for x in outs if pid(x)}
events=defaultdict(list); under=defaultdict(list)
for r in micro:
    try:e=float(str(r["observed_at"]).replace("Z","+00:00").split("+")[0].replace(" ","T") and __import__("datetime").datetime.fromisoformat(str(r["observed_at"]).replace("Z","+00:00")).timestamp())
    except:
        try:e=float(r.get("observed_epoch"))
        except:continue
    r["_e"]=e; events[r["ticker"]].append(r)
    u="BTC" if r["ticker"].startswith("KXBTC") else ("ETH" if r["ticker"].startswith("KXETH") else ("SOL" if r["ticker"].startswith("KXSOL") else "OTHER"))
    if u!="OTHER":under[u].append(r)
for d in (events,under):
    for k in d:d[k].sort(key=lambda z:z["_e"])

cb=defaultdict(list)
for r in loadj(COINBASE):
    try:
        if not r.get("full_horizon_complete") or not r.get("past_only"):continue
        cb[(str(r["product_id"]),int(r["window_seconds"]))].append((float(r["anchor_epoch"]),float(r["return"]),float(r.get("boundary_age_seconds",0))))
    except:pass
for k in cb:cb[k].sort()

def win(arr,e,w):
    ts=[x["_e"] for x in arr]
    a=bisect.bisect_left(ts,e-w); b=bisect.bisect_right(ts,e)
    return arr[a:b]

def features(arr,e,w):
    z=win(arr,e,w); trades=[x for x in z if x["observation_type"]=="trade"]
    px=[x["yes_reference"] for x in z if x.get("yes_reference") is not None]
    spr=[x["yes_ask"]-x["yes_bid"] for x in z if x.get("yes_ask") is not None and x.get("yes_bid") is not None]
    vol=sum(float(x.get("trade_size") or 0) for x in trades)
    y=sum(int(x.get("taker_yes") or 0) for x in trades); n=sum(int(x.get("taker_no") or 0) for x in trades)
    return {"trade_count":len(trades),"trade_volume":vol,"taker_imbalance":(y-n)/max(1,y+n),
            "yes_return":(px[-1]-px[0]) if len(px)>=2 else 0.0,
            "spread_last":spr[-1] if spr else None,"spread_mean":sum(spr)/len(spr) if spr else None,
            "yes_price_last":px[-1] if px else None}

def cbret(product,w,e):
    a=cb.get((product,w),[])
    if not a:return None
    i=bisect.bisect_right(a,(e,1e99,1e99))-1
    return a[i][1] if i>=0 else None

rows=[]
for k,o in oby.items():
    p=pby.get(k)
    if not p:continue
    e=epoch(p); t=ticker(p); h=horizon(p); fr=future_ret(o)
    if e is None or not t or h is None or fr is None:continue
    u="BTC" if t.startswith("KXBTC") else ("ETH" if t.startswith("KXETH") else ("SOL" if t.startswith("KXSOL") else None))
    if not u:continue
    r={"prediction_id":k,"ticker":t,"underlying":u,"decision_epoch":e,"horizon_seconds":h,"future_return":fr}
    for w in WINDOWS:
        for n,v in features(events.get(t,[]),e,w).items():r[f"self_{w}s_{n}"]=v
        for n,v in features(under.get(u,[]),e,w).items():
            if n in ("trade_count","trade_volume","taker_imbalance","yes_return"):r[f"sibling_{w}s_{n}"]=v
    dt=__import__("datetime").datetime.fromtimestamp(e)
    r["minute_of_day"]=dt.hour*60+dt.minute; r["weekday"]=dt.weekday()
    for w in (5,15,30,60):r[f"coinbase_{w}s_return"]=cbret(u+"-USD",w,e)
    rows.append(r)

OUT.parent.mkdir(parents=True,exist_ok=True)
rows.sort(key=lambda x:x["decision_epoch"])
with OUT.open("w",encoding="utf-8") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"))+"\n")
print("[PREDICTIONS]",len(preds),"[OUTCOMES]",len(outs),"[JOINED FEATURE ROWS]",len(rows))
print("[FEATURE FAMILIES] trade-flow / volume / timing / spread / sibling-lead-lag / Coinbase-lead-lag")
print("[RESULT] STRATEGY_FEATURE_CORPUS_READY" if rows else "[RESULT] NO_JOINED_FEATURE_ROWS")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
