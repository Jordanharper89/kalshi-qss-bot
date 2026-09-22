from pathlib import Path
import json, datetime, statistics
from collections import defaultdict, deque

ROOT = Path(__file__).resolve().parents[2]
PRED = ROOT / "runtime" / "predictive_data" / "opd_full_evidence_live_prediction_ledger.jsonl"
OUTC = ROOT / "runtime" / "predictive_data" / "opd_full_evidence_live_outcome_ledger.jsonl"
ARCHIVE = ROOT / "runtime" / "strategy_discovery" / "osd_001_kalshi_microstructure_archive.jsonl"
DEST = ROOT / "runtime" / "strategy_discovery" / "osd_002_strategy_feature_corpus.jsonl"
SUMMARY = ROOT / "runtime" / "strategy_discovery" / "osd_002_strategy_feature_corpus_summary.json"

WINDOWS = (5,15,30,60,300)
MAX_WINDOW = 300

def load_jsonl(path):
    out=[]
    with path.open("r",encoding="utf-8") as f:
        for line in f:
            try:
                x=json.loads(line)
                if isinstance(x,dict): out.append(x)
            except Exception:
                pass
    return out

def asset_of(ticker):
    u=(ticker or "").upper()
    if u.startswith("KXBTC"): return "BTC"
    if u.startswith("KXETH"): return "ETH"
    if u.startswith("KXSOL"): return "SOL"
    return None

def to_epoch(v):
    if v is None: return None
    if isinstance(v,(int,float)): return float(v)
    s=str(v).strip()
    try: return float(s)
    except Exception: pass
    try:
        if s.endswith("Z"): s=s[:-1]+"+00:00"
        return datetime.datetime.fromisoformat(s).timestamp()
    except Exception:
        return None

def feature_stats(xs,t0,w):
    lo=t0-w
    ys=[x for x in xs if x["ts"] is not None and lo <= x["ts"] <= t0]
    tr=[x for x in ys if x["type"]=="trade"]
    refs=[]; spreads=[]
    for x in ys:
        p=x["trade"]
        if p is None and x["bid"] is not None and x["ask"] is not None:
            p=(x["bid"]+x["ask"])/2.0
        if p is not None: refs.append((x["ts"],p))
        if x["bid"] is not None and x["ask"] is not None:
            spreads.append(x["ask"]-x["bid"])
    refs.sort()
    yes=sum(x["taker_yes"] for x in tr); no=sum(x["taker_no"] for x in tr); den=yes+no
    ret=None
    if len(refs)>=2 and refs[0][1]: ret=refs[-1][1]/refs[0][1]-1.0
    return {"trade_count":len(tr),"trade_volume":sum(x["size"] for x in tr),"taker_imbalance":((yes-no)/den) if den else 0.0,
            "yes_return":ret,"spread_last":spreads[-1] if spreads else None,"spread_mean":statistics.fmean(spreads) if spreads else None,
            "yes_last":refs[-1][1] if refs else None}

def normalize_archive_row(r):
    return {"seq":int(r.get("sequence_number") or 0),"type":str(r.get("observation_type") or ""),"ts":to_epoch(r.get("observed_at")),
            "ticker":str(r.get("ticker") or ""),"asset":asset_of(r.get("ticker")),"bid":r.get("yes_bid"),"ask":r.get("yes_ask"),
            "trade":r.get("yes_trade_price"),"size":float(r.get("trade_size") or 0.0),"taker_yes":int(r.get("taker_yes") or 0),
            "taker_no":int(r.get("taker_no") or 0)}

def main():
    preds=load_jsonl(PRED)
    outs={str(x.get("prediction_id")):x for x in load_jsonl(OUTC) if x.get("prediction_id")}
    anchors=[]
    for p in preds:
        pid=str(p.get("prediction_id") or ""); o=outs.get(pid)
        if not o: continue
        try: seq=int(p.get("anchor_sequence_boundary") or 0)
        except Exception: seq=0
        t=to_epoch(p.get("prediction_frozen_epoch") or p.get("anchor_observed_epoch")); ticker=str(p.get("ticker") or "")
        try: y=float(o.get("future_return"))
        except Exception: y=None
        if seq>0 and t is not None and ticker and y is not None:
            anchors.append({"seq":seq,"t":t,"ticker":ticker,"asset":p.get("asset") or asset_of(ticker),"prediction_id":pid,
                            "horizon_seconds":p.get("horizon_seconds"),"future_return":y})
    anchors.sort(key=lambda x:x["seq"])
    print("[PREDICTIONS]",len(preds),flush=True); print("[OUTCOMES]",len(outs),flush=True); print("[JOINABLE EXACT-ANCHOR ROWS]",len(anchors),flush=True)
    if not anchors: raise SystemExit("[FAIL] zero exact-anchor joins")

    active_tickers=set(a["ticker"] for a in anchors); active_assets=set(a["asset"] for a in anchors if a["asset"])
    ticker_q=defaultdict(deque); asset_q=defaultdict(deque)
    DEST.parent.mkdir(parents=True,exist_ok=True); tmp=DEST.with_suffix(".tmp")
    ai=0; scanned=0; kept=0; written=0

    def expire(q,t):
        cutoff=t-MAX_WINDOW
        while q and q[0]["ts"] is not None and q[0]["ts"] < cutoff: q.popleft()

    def emit(a,f):
        nonlocal written
        tq=ticker_q[a["ticker"]]; aq=asset_q[a["asset"]] if a["asset"] else ()
        feat={}
        for w in WINDOWS:
            s=feature_stats(tq,a["t"],w)
            for k,v in s.items(): feat[f"self_{w}s_{k}"]=v
            if a["asset"]:
                sib=[x for x in aq if x["ticker"] != a["ticker"]]
                s2=feature_stats(sib,a["t"],w)
                for k,v in s2.items(): feat[f"sibling_{w}s_{k}"]=v
        dt=datetime.datetime.fromtimestamp(a["t"],datetime.timezone.utc)
        feat["minute_of_day"]=dt.hour*60+dt.minute; feat["weekday"]=dt.weekday()
        row=dict(a); row["features"]=feat; row["execution_authority"]=False; row["publication_allowed"]=False
        f.write(json.dumps(row,separators=(",",":"))+"\n"); written+=1

    with ARCHIVE.open("r",encoding="utf-8") as src, tmp.open("w",encoding="utf-8") as out:
        for line in src:
            scanned+=1
            try: r=normalize_archive_row(json.loads(line))
            except Exception: continue
            if r["seq"]<=0 or r["ts"] is None: continue
            while ai < len(anchors) and anchors[ai]["seq"] < r["seq"]:
                a=anchors[ai]; expire(ticker_q[a["ticker"]],a["t"])
                if a["asset"]: expire(asset_q[a["asset"]],a["t"])
                emit(a,out); ai+=1
            if r["ticker"] in active_tickers or r["asset"] in active_assets:
                expire(ticker_q[r["ticker"]],r["ts"]); ticker_q[r["ticker"]].append(r)
                if r["asset"]:
                    expire(asset_q[r["asset"]],r["ts"]); asset_q[r["asset"]].append(r)
                kept+=1
            if scanned % 500000 == 0:
                print(f"[ARCHIVE SCANNED] {scanned} [KEPT] {kept} [FEATURE_ROWS] {written}/{len(anchors)}",flush=True)
        while ai < len(anchors):
            a=anchors[ai]; expire(ticker_q[a["ticker"]],a["t"])
            if a["asset"]: expire(asset_q[a["asset"]],a["t"])
            emit(a,out); ai+=1

    tmp.replace(DEST)
    SUMMARY.write_text(json.dumps({"revision":"OSD_002_STREAMING_SWEEP_V1","archive_rows_scanned":scanned,"relevant_rows_kept":kept,
                                   "joined_feature_rows":written,"windows_seconds":list(WINDOWS),"single_pass_archive":True,
                                   "future_outcome_feature_leakage":False,"execution_authority":False,"publication_allowed":False},indent=2),encoding="utf-8")
    print("[ARCHIVE ROWS SCANNED]",scanned); print("[RELEVANT MICROSTRUCTURE ROWS]",kept); print("[JOINED FEATURE ROWS]",written)
    print("[RESULT] DECISION_TIME_FEATURE_CORPUS_READY"); print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__": main()
