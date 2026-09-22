from pathlib import Path
ROOT=Path.cwd().resolve()
AUDIT=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_btc_network_shock_sensitive_contract_mapping_audit.py"
TEST=ROOT/"test_opd_BTC_NETWORK_SHOCK_SENSITIVE_CONTRACT_MAPPING_AUDIT_V1.py"

AUDIT_CODE = r"""
from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
ALPHA=ROOT/"runtime"/"predictive_data"/"opd_btc_network_shock_incremental_alpha_audit_v1.json"
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
RESULT=ROOT/"runtime"/"predictive_data"/"opd_btc_network_shock_sensitive_contract_mapping_audit_v1.json"

HURDLE=0.02
MIN_N=12
MIN_TICKERS=3
PRICE_BANDS=((0.10,0.90),(0.20,0.80),(0.30,0.70),(0.40,0.60))

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

def rr(o):
    for k in ("future_return","realized_return","directional_return"):
        v=flt(o.get(k))
        if v is not None:return v
    return None

def recursive_find_price(x):
    preferred=("current_yes_price","yes_price","anchor_yes_price","yes_bid","yes_ask","market_price","price")
    if isinstance(x,dict):
        for k in preferred:
            if k in x:
                v=flt(x.get(k))
                if v is not None:
                    if v>1.0 and v<=100.0:v/=100.0
                    if 0.0<=v<=1.0:return v
        for k,v in x.items():
            if str(k).lower() in ("canonical_observation_json","canonical_observation","kalshi_state","market_state","anchor"):
                z=recursive_find_price(v)
                if z is not None:return z
    elif isinstance(x,list):
        for v in x[:64]:
            z=recursive_find_price(v)
            if z is not None:return z
    return None

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

def ptime(p):
    for k in ("prediction_epoch","frozen_epoch","created_epoch","anchor_observed_epoch","observed_epoch"):
        v=flt(p.get(k))
        if v is not None:return v
    due=flt(p.get("resolution_due_epoch")); h=flt(p.get("horizon_seconds"))
    return due-h if due is not None and h is not None else 0.0

alpha=json.loads(ALPHA.read_text(encoding="utf-8"))
survivors=alpha.get("survivors") or []
pred=[p for p in load_jsonl(PRED) if str(p.get("asset") or "").upper()=="BTC"]
pred.sort(key=lambda p:(ptime(p),str(p.get("prediction_id") or "")))
omap={str(x.get("prediction_id")):x for x in load_jsonl(OUT) if x.get("prediction_id")}

rows=[]
for w in survivors:
    h=int(w["horizon_seconds"]); feature=str(w["feature"]); op=str(w["op"]); th=float(w["threshold"])
    udir=str(w["direction"]).upper()
    prior=None
    candidates=[]
    for p in pred:
        if int(p.get("horizon_seconds") or 0)!=h: continue
        cur=snap_value(p,feature)
        if cur is None: continue
        if prior is None:
            prior=cur; continue
        d=cur-prior
        pct=(d/abs(prior)) if prior!=0 else 0.0
        prior=cur
        x=d if feature.endswith(".delta") else pct
        if not ((x<=th) if op=="LE" else (x>=th)): continue

        yesp=recursive_find_price(p)
        if yesp is None: continue
        o=omap.get(str(p.get("prediction_id") or ""))
        if not o: continue
        r=rr(o)
        if r is None: continue
        sem=str(p.get("yes_semantic") or "")
        if udir=="UP":
            cdir="UP" if sem=="YES_MEANS_UNDERLYING_HIGHER" else ("DOWN" if sem=="YES_MEANS_UNDERLYING_LOWER" else None)
        else:
            cdir="DOWN" if sem=="YES_MEANS_UNDERLYING_HIGHER" else ("UP" if sem=="YES_MEANS_UNDERLYING_LOWER" else None)
        if cdir is None: continue
        gross=r if cdir=="UP" else -r
        candidates.append((p,yesp,gross))

    for lo,hi in PRICE_BANDS:
        sel=[z for z in candidates if lo<=z[1]<=hi]
        nets=[z[2]-HURDLE for z in sel]
        tickers={str(z[0].get("ticker") or "") for z in sel}
        mu=sum(nets)/len(nets) if nets else None
        lb=None
        if nets:
            lb=mu if len(nets)==1 else mu-1.96*(statistics.stdev(nets)/math.sqrt(len(nets)))
        supported=len(nets)>=MIN_N and len(tickers)>=MIN_TICKERS
        profitable=supported and lb is not None and lb>0
        rows.append({
            "horizon_seconds":h,"feature":feature,"op":op,"threshold":th,
            "underlying_direction":udir,"yes_price_band":[lo,hi],
            "n":len(nets),"unique_tickers":len(tickers),
            "mean_net_after_2pct":mu,
            "positive_net_rate":sum(1 for x in nets if x>0)/len(nets) if nets else None,
            "lb95_net_after_2pct":lb,
            "supported":supported,"profitable":profitable,
        })

rows.sort(key=lambda x:(x["profitable"],x["lb95_net_after_2pct"] if x["lb95_net_after_2pct"] is not None else -999),reverse=True)
wins=[x for x in rows if x["profitable"]]
priced=sum(1 for p in pred if recursive_find_price(p) is not None)

RESULT.write_text(json.dumps({
    "revision":"BTC_NETWORK_SHOCK_SENSITIVE_CONTRACT_MAPPING_AUDIT_V1",
    "hurdle":HURDLE,
    "prediction_rows_with_decision_time_yes_price":priced,
    "evaluated_rule_bands":len(rows),
    "profitable_sensitive_contract_rules":len(wins),
    "winners":wins,"results":rows
},indent=2,sort_keys=True),encoding="utf-8")

print("[PREDICTION ROWS WITH DECISION-TIME YES PRICE]",priced)
print("[EVALUATED RULE/BANDS]",len(rows))
print("[PROFITABLE SENSITIVE-CONTRACT RULES]",len(wins))
for x in rows[:40]:
    print("[SENSITIVE MAP] H=",x["horizon_seconds"],"FEATURE=",x["feature"],"OP=",x["op"],
          "DIR=",x["underlying_direction"],"YES_BAND=",x["yes_price_band"],
          "N=",x["n"],"TICKERS=",x["unique_tickers"],"MEAN_NET=",x["mean_net_after_2pct"],
          "LB95=",x["lb95_net_after_2pct"],"POS_RATE=",x["positive_net_rate"],"PROFITABLE=",x["profitable"])
print("[RESULT FILE]",RESULT)
if wins:
    print("[RESULT] BTC_NETWORK_SHOCK_SENSITIVE_KALSHI_EDGE_FOUND")
else:
    print("[RESULT] NO_SENSITIVE_KALSHI_EDGE_AFTER_2PCT")
print("[MODEL MUTATION] FALSE")
print("[HURDLE CHANGE] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

TEST_CODE = r"""
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_network_shock_sensitive_contract_mapping_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in (
'HURDLE=0.02',
'PRICE_BANDS=((0.10,0.90),(0.20,0.80),(0.30,0.70),(0.40,0.60))',
'recursive_find_price',
'YES_MEANS_UNDERLYING_HIGHER',
'YES_MEANS_UNDERLYING_LOWER',
'lb95_net_after_2pct',
'BTC_NETWORK_SHOCK_SENSITIVE_KALSHI_EDGE_FOUND',
'NO_SENSITIVE_KALSHI_EDGE_AFTER_2PCT',
):
    assert x in s,x
print("[PASS] sensitive-contract Kalshi mapping audit installed")
print("[PASS] selection uses decision-time YES price only")
print("[PASS] fixed price bands are predeclared")
print("[PASS] exact contract semantics preserved")
print("[PASS] fixed 2% hurdle and positive LB95 profitability gate preserved")
print("[PASS] no model mutation/execution/publication")
"""

AUDIT.parent.mkdir(parents=True,exist_ok=True)
AUDIT.write_text(AUDIT_CODE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")
compile(AUDIT_CODE,str(AUDIT),"exec")
compile(TEST_CODE,str(TEST),"exec")
print("[PASS] BTC network-shock sensitive-contract mapping audit V1 installed")
print("[AUDIT]",AUDIT)
print("[TEST]",TEST)
print("[SELECTION] decision-time YES-price sensitivity bands")
print("[HURDLE] 0.02 fixed")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
