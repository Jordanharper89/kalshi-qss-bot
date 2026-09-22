
from pathlib import Path
import json, math, statistics, sys

ROOT=Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
ALPHA=ROOT/"runtime"/"predictive_data"/"opd_btc_network_shock_incremental_alpha_audit_v1.json"
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
RESULT=ROOT/"runtime"/"predictive_data"/"opd_btc_kalshi_exact_price_profitability_gate_v1.json"

HURDLE=0.02
MIN_N=12
MIN_TICKERS=3
PRICE_BANDS=((0.10,0.90),(0.20,0.80),(0.30,0.70),(0.40,0.60))
KALSHI_SOURCE="source.kalshi.market_data"

def load_jsonl(p):
    out=[]
    if not p.exists(): return out
    for line in p.read_text(encoding="utf-8").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def flt(x):
    try:
        if isinstance(x,bool): return None
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:return None

def ptime(p):
    for k in ("prediction_epoch","frozen_epoch","created_epoch","anchor_observed_epoch","observed_epoch"):
        v=flt(p.get(k))
        if v is not None:return v
    due=flt(p.get("resolution_due_epoch")); h=flt(p.get("horizon_seconds"))
    return due-h if due is not None and h is not None else None

def anchor_seq(p):
    for k in ("anchor_sequence","anchor_sequence_number","sequence_number"):
        try:
            v=int(p.get(k))
            if v>0:return v
        except Exception: pass
    for container in ("anchor","lineage","state_lineage","kalshi_state"):
        x=p.get(container)
        if isinstance(x,dict):
            for k in ("anchor_sequence","anchor_sequence_number","sequence_number"):
                try:
                    v=int(x.get(k))
                    if v>0:return v
                except Exception: pass
    return None

def rr(o):
    for k in ("future_return","realized_return","directional_return"):
        v=flt(o.get(k))
        if v is not None:return v
    return None

def yes_semantic(p):
    s=str(p.get("yes_semantic") or "")
    if s:return s
    for c in ("contract_semantics","market_semantics","kalshi_state","anchor"):
        x=p.get(c)
        if isinstance(x,dict):
            s=str(x.get("yes_semantic") or "")
            if s:return s
    return ""

def extract_ticker(x):
    if isinstance(x,dict):
        for k in ("ticker","market_ticker","contract_ticker","symbol"):
            v=x.get(k)
            if isinstance(v,str) and v:return v
        for v in x.values():
            r=extract_ticker(v)
            if r:return r
    elif isinstance(x,list):
        for v in x[:64]:
            r=extract_ticker(v)
            if r:return r
    return None

def normalize_price(v):
    x=flt(v)
    if x is None:return None
    if 1.0 < x <= 100.0:x/=100.0
    return x if 0.0 <= x <= 1.0 else None

def _walk_dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            yield from _walk_dicts(v)
    elif isinstance(x,list):
        for v in x[:128]:
            yield from _walk_dicts(v)

def _best_level(x):
    vals=[]
    if isinstance(x,list):
        for item in x[:256]:
            if isinstance(item,(list,tuple)) and item:
                p=normalize_price(item[0])
                if p is not None: vals.append(p)
            elif isinstance(item,dict):
                for k in ("price","yes_price","p"):
                    if k in item:
                        p=normalize_price(item.get(k))
                        if p is not None: vals.append(p); break
    return max(vals) if vals else None

def extract_yes_price(x,observation_type=""):
    typ=str(observation_type or "").lower()

    explicit=(
        "yes_price","yes_bid","yes_ask","yes_bid_price","yes_ask_price","yes_price_dollars","yes_bid_dollars","yes_ask_dollars",
        "best_yes_bid","best_yes_ask","last_yes_price","yes_last_price"
    )
    for d in _walk_dicts(x):
        bid=ask=None
        for k in ("yes_bid","yes_bid_price","best_yes_bid","yes_bid_dollars"):
            if k in d:
                bid=normalize_price(d.get(k))
                if bid is not None: break
        for k in ("yes_ask","yes_ask_price","best_yes_ask","yes_ask_dollars"):
            if k in d:
                ask=normalize_price(d.get(k))
                if ask is not None: break
        if bid is not None and ask is not None:
            return (bid+ask)/2.0

        for k in explicit:
            if k in d:
                p=normalize_price(d.get(k))
                if p is not None:return p

    if "trade" in typ or "ticker" in typ:
        for d in _walk_dicts(x):
            for k in ("yes_price_dollars","price_dollars","price","last_price","market_price"):
                if k in d:
                    p=normalize_price(d.get(k))
                    if p is not None:return p

    if "orderbook" in typ:
        for d in _walk_dicts(x):
            for k in ("yes","yes_bids","yes_orders","yes_levels"):
                if k in d:
                    p=_best_level(d.get(k))
                    if p is not None:return p

    return None

def connect_db():
    import importlib, re
    prod=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
    txt=prod.read_text(encoding="utf-8")
    patterns=(
        r"from\s+([A-Za-z0-9_\.]+)\s+import\s+connect\s+as\s+_opd_exo_connect",
        r"from\s+([A-Za-z0-9_\.]+)\s+import\s+connect",
    )
    errors=[]
    for pat in patterns:
        m=re.search(pat,txt)
        if not m: continue
        modname=m.group(1)
        try:
            mod=importlib.import_module(modname)
            fn=getattr(mod,"connect")
            return fn()
        except Exception as e:
            errors.append(f"{modname}: {type(e).__name__}: {e}")
    raise RuntimeError("production PostgreSQL connector unresolved from predictor source; "+" | ".join(errors))

SQL_EXACT_PRICE=(
    "SELECT sequence_number, observation_type, canonical_observation_json "
    "FROM public.oracle_canonical_observations "
    "WHERE source_id=%s "
    "AND sequence_number<=%s "
    "AND observed_at<=to_timestamp(%s) "
    "ORDER BY sequence_number DESC "
    "LIMIT 250"
)

def derive_anchor_sequence(cur,ticker,obs_epoch):
    if not ticker or obs_epoch is None:return None
    cur.execute(
        "SELECT sequence_number, canonical_observation_json "
        "FROM public.oracle_canonical_observations "
        "WHERE source_id=%s "
        "AND observed_at<=to_timestamp(%s) "
        "ORDER BY sequence_number DESC "
        "LIMIT 500",
        (KALSHI_SOURCE,float(obs_epoch))
    )
    for sn,obj in cur.fetchall():
        if isinstance(obj,str):
            try: obj=json.loads(obj)
            except Exception: continue
        if extract_ticker(obj)==ticker:
            return int(sn)
    return None

def exact_yes_price(cur,ticker,seq,obs_epoch):
    if not ticker or obs_epoch is None:return None,None,None
    if seq is None:
        seq=derive_anchor_sequence(cur,ticker,obs_epoch)
    if seq is None:return None,None,None
    cur.execute(SQL_EXACT_PRICE,(KALSHI_SOURCE,int(seq),float(obs_epoch)))
    for sn,observation_type,obj in cur.fetchall():
        if isinstance(obj,str):
            try: obj=json.loads(obj)
            except Exception: continue
        if extract_ticker(obj)!=ticker: continue
        px=extract_yes_price(obj,observation_type)
        if px is not None:return px,int(sn),int(seq)
    return None,None,int(seq)

def snap_value(p,feature):
    metric=feature.split(".",1)[0]
    for v in (p.get("exogenous_evidence_snapshot") or {}).values():
        if not isinstance(v,dict): continue
        sid=str(v.get("source_id") or "")
        if not sid.endswith("."+metric): continue
        stack=[v.get("canonical_observation")]
        while stack:
            x=stack.pop()
            if isinstance(x,dict):
                if "value" in x:
                    z=flt(x.get("value"))
                    if z is not None:return z
                stack.extend(x.values())
            elif isinstance(x,list): stack.extend(x[:32])
    return None

alpha=json.loads(ALPHA.read_text(encoding="utf-8"))
survivors=alpha.get("survivors") or []
pred=[p for p in load_jsonl(PRED) if str(p.get("asset") or "").upper()=="BTC"]
pred.sort(key=lambda p:(ptime(p) or 0.0,str(p.get("prediction_id") or "")))
omap={str(x.get("prediction_id")):x for x in load_jsonl(OUT) if x.get("prediction_id")}

con=connect_db()
cur=con.cursor()

price_cache={}
price_recovered=0
anchor_missing=0
anchor_derived=0

def get_price(p):
    global price_recovered,anchor_missing,anchor_derived
    pid=str(p.get("prediction_id") or "")
    if pid in price_cache:return price_cache[pid]
    t=ptime(p); seq=anchor_seq(p); ticker=str(p.get("ticker") or "")
    if t is None or not ticker:
        anchor_missing+=1
        price_cache[pid]=(None,None)
        return price_cache[pid]
    stored_seq=seq
    px,sn,used_seq=exact_yes_price(cur,ticker,seq,t)
    if stored_seq is None and used_seq is not None:
        anchor_derived+=1
    if used_seq is None:
        anchor_missing+=1
    if px is not None:
        price_recovered+=1
    price_cache[pid]=(px,sn)
    return price_cache[pid]

results=[]
for w in survivors:
    h=int(w["horizon_seconds"])
    feature=str(w["feature"])
    op=str(w["op"])
    th=float(w["threshold"])
    udir=str(w["direction"]).upper()
    prior=None
    candidates=[]

    for p in pred:
        if int(p.get("horizon_seconds") or 0)!=h: continue
        curv=snap_value(p,feature)
        if curv is None: continue
        if prior is None:
            prior=curv
            continue

        d=curv-prior
        pct=(d/abs(prior)) if prior!=0 else 0.0
        prior=curv
        x=d if feature.endswith(".delta") else pct
        if not ((x<=th) if op=="LE" else (x>=th)): continue

        o=omap.get(str(p.get("prediction_id") or ""))
        if not o: continue
        r=rr(o)
        if r is None: continue

        sem=yes_semantic(p)
        if udir=="UP":
            cdir="UP" if sem=="YES_MEANS_UNDERLYING_HIGHER" else ("DOWN" if sem=="YES_MEANS_UNDERLYING_LOWER" else None)
        else:
            cdir="DOWN" if sem=="YES_MEANS_UNDERLYING_HIGHER" else ("UP" if sem=="YES_MEANS_UNDERLYING_LOWER" else None)
        if cdir is None: continue

        px,price_seq=get_price(p)
        if px is None: continue

        gross=r if cdir=="UP" else -r
        candidates.append({
            "ticker":str(p.get("ticker") or ""),
            "prediction_id":p.get("prediction_id"),
            "decision_yes_price":px,
            "decision_price_sequence":price_seq,
            "gross_directional_return":gross,
            "net_after_2pct":gross-HURDLE,
        })

    for lo,hi in PRICE_BANDS:
        sel=[z for z in candidates if lo<=z["decision_yes_price"]<=hi]
        nets=[z["net_after_2pct"] for z in sel]
        tickers={z["ticker"] for z in sel}
        mu=sum(nets)/len(nets) if nets else None
        lb=None
        if nets:
            lb=mu if len(nets)==1 else mu-1.96*(statistics.stdev(nets)/math.sqrt(len(nets)))
        supported=len(nets)>=MIN_N and len(tickers)>=MIN_TICKERS
        profitable=supported and lb is not None and lb>0
        results.append({
            "horizon_seconds":h,
            "feature":feature,
            "op":op,
            "threshold":th,
            "underlying_direction":udir,
            "yes_price_band":[lo,hi],
            "n":len(nets),
            "unique_tickers":len(tickers),
            "mean_net_after_2pct":mu,
            "positive_net_rate":sum(1 for x in nets if x>0)/len(nets) if nets else None,
            "cumulative_net_after_2pct":sum(nets),
            "lb95_net_after_2pct":lb,
            "supported":supported,
            "profitable":profitable,
        })

cur.close()
try: con.close()
except Exception: pass

results.sort(
    key=lambda x:(x["profitable"],
                  x["lb95_net_after_2pct"] if x["lb95_net_after_2pct"] is not None else -999),
    reverse=True
)
wins=[x for x in results if x["profitable"]]

payload={
    "revision":"BTC_KALSHI_EXACT_PRICE_PROFITABILITY_GATE_V1",
    "hurdle":HURDLE,
    "incremental_alpha_survivors":len(survivors),
    "decision_time_yes_prices_recovered":price_recovered,
    "prediction_rows_missing_anchor_lineage":anchor_missing,
    "decision_time_anchors_derived_from_canonical":anchor_derived,
    "evaluated_rule_bands":len(results),
    "profitable_rule_bands":len(wins),
    "winners":wins,
    "results":results,
}
RESULT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

print("[UNDERLYING SURVIVORS]",len(survivors))
print("[DECISION-TIME YES PRICES RECOVERED]",price_recovered)
print("[DECISION-TIME ANCHORS DERIVED FROM CANONICAL]",anchor_derived)
print("[PREDICTION ROWS MISSING ANCHOR LINEAGE]",anchor_missing)
print("[EVALUATED RULE/BANDS]",len(results))
print("[PROFITABLE KALSHI RULE/BANDS]",len(wins))

for x in results[:40]:
    print("[EDGE] H=",x["horizon_seconds"],
          "FEATURE=",x["feature"],
          "OP=",x["op"],
          "DIR=",x["underlying_direction"],
          "YES_BAND=",x["yes_price_band"],
          "N=",x["n"],
          "TICKERS=",x["unique_tickers"],
          "MEAN_NET=",x["mean_net_after_2pct"],
          "LB95=",x["lb95_net_after_2pct"],
          "POS_RATE=",x["positive_net_rate"],
          "PROFITABLE=",x["profitable"])

print("[RESULT FILE]",RESULT)
if wins:
    print("[RESULT] KALSHI_PROFITABLE_EDGE_CANDIDATE_FOUND")
else:
    print("[RESULT] NO_KALSHI_PROFITABLE_EDGE_FOUND")
print("[HURDLE] 0.02")
print("[MODEL MUTATION] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
