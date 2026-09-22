
from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
ALPHA=ROOT/"runtime"/"predictive_data"/"opd_btc_network_shock_incremental_alpha_audit_v1.json"
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
RESULT=ROOT/"runtime"/"predictive_data"/"opd_btc_network_shock_kalshi_mapping_audit_v1.json"

HURDLE=0.02
MIN_N=12
MIN_TICKERS=3

def load_jsonl(p):
    rows=[]
    if not p.exists(): return rows
    for line in p.read_text(encoding="utf-8").splitlines():
        try: rows.append(json.loads(line))
        except Exception: pass
    return rows

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

def snap_value(p, feature):
    metric=feature.split(".",1)[0]
    kind=feature.split(".",1)[1]
    for v in (p.get("exogenous_evidence_snapshot") or {}).values():
        if not isinstance(v,dict): continue
        sid=str(v.get("source_id") or "")
        if not sid.endswith("."+metric): continue
        obj=v.get("canonical_observation")
        stack=[obj]
        val=None
        while stack:
            x=stack.pop()
            if isinstance(x,dict):
                if "value" in x:
                    z=flt(x.get("value"))
                    if z is not None:
                        val=z; break
                stack.extend(x.values())
            elif isinstance(x,list): stack.extend(x[:32])
        return val
    return None

alpha=json.loads(ALPHA.read_text(encoding="utf-8"))
survivors=alpha.get("survivors") or []
pred=load_jsonl(PRED)
omap={str(x.get("prediction_id")):x for x in load_jsonl(OUT) if x.get("prediction_id")}

# Build prior value per metric from prediction chronology, then apply frozen survivor semantics.
def ptime(p):
    for k in ("prediction_epoch","frozen_epoch","created_epoch","anchor_observed_epoch","observed_epoch"):
        v=flt(p.get(k))
        if v is not None:return v
    due=flt(p.get("resolution_due_epoch")); h=flt(p.get("horizon_seconds"))
    return due-h if due is not None and h is not None else 0.0

btc=[p for p in pred if str(p.get("asset") or "").upper()=="BTC"]
btc.sort(key=lambda p:(ptime(p),str(p.get("prediction_id") or "")))

results=[]
for w in survivors:
    h=int(w["horizon_seconds"])
    feature=str(w["feature"])
    metric=feature.split(".",1)[0]
    op=str(w["op"])
    th=float(w["threshold"])
    underlying_dir=str(w["direction"]).upper()
    prior=None
    matched=[]
    for p in btc:
        if int(p.get("horizon_seconds") or 0)!=h: continue
        cur=snap_value(p,feature)
        if cur is None: continue
        if prior is None:
            prior=cur; continue
        delta=cur-prior
        pct=(delta/abs(prior)) if prior!=0 else 0.0
        prior=cur
        x=delta if feature.endswith(".delta") else pct
        ok=(x<=th) if op=="LE" else (x>=th)
        if not ok: continue
        o=omap.get(str(p.get("prediction_id") or ""))
        if not o: continue
        r=rr(o)
        if r is None: continue

        # Map underlying direction to exact contract YES semantics.
        sem=str(p.get("yes_semantic") or "")
        if underlying_dir=="UP":
            if sem=="YES_MEANS_UNDERLYING_HIGHER": cdir="UP"
            elif sem=="YES_MEANS_UNDERLYING_LOWER": cdir="DOWN"
            else: continue
        else:
            if sem=="YES_MEANS_UNDERLYING_HIGHER": cdir="DOWN"
            elif sem=="YES_MEANS_UNDERLYING_LOWER": cdir="UP"
            else: continue

        gross=r if cdir=="UP" else -r
        matched.append({
            "ticker":str(p.get("ticker") or ""),
            "prediction_id":p.get("prediction_id"),
            "contract_direction":cdir,
            "gross_directional_return":gross,
            "net_after_2pct":gross-HURDLE,
        })

    nets=[x["net_after_2pct"] for x in matched]
    tickers={x["ticker"] for x in matched}
    mu=sum(nets)/len(nets) if nets else None
    if nets:
        lb=mu if len(nets)==1 else mu-1.96*(statistics.stdev(nets)/math.sqrt(len(nets)))
    else: lb=None
    supported=len(nets)>=MIN_N and len(tickers)>=MIN_TICKERS
    profitable=supported and lb is not None and lb>0
    results.append({
        "source_rule":w,
        "mapped_n":len(nets),
        "unique_tickers":len(tickers),
        "mean_net_after_2pct":mu,
        "positive_net_rate":sum(1 for x in nets if x>0)/len(nets) if nets else None,
        "cumulative_net_after_2pct":sum(nets),
        "lb95_net_after_2pct":lb,
        "supported":supported,
        "profitable_supported":profitable,
    })

results.sort(key=lambda x:(x["profitable_supported"],x["lb95_net_after_2pct"] if x["lb95_net_after_2pct"] is not None else -999),reverse=True)
wins=[x for x in results if x["profitable_supported"]]
payload={
"revision":"BTC_NETWORK_SHOCK_KALSHI_MAPPING_AUDIT_V1",
"hurdle":HURDLE,
"incremental_alpha_survivors":len(survivors),
"mapped_rules":len(results),
"profitable_mapped_rules":len(wins),
"winners":wins,
"results":results,
}
RESULT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

print("[INCREMENTAL ALPHA SURVIVORS]",len(survivors))
print("[KALSHI MAPPED RULES]",len(results))
print("[PROFITABLE KALSHI MAPPED RULES]",len(wins))
for x in results[:30]:
    w=x["source_rule"]
    print("[MAP] H=",w["horizon_seconds"],"FEATURE=",w["feature"],"OP=",w["op"],"TH=",w["threshold"],
          "UNDERLYING_DIR=",w["direction"],"N=",x["mapped_n"],"TICKERS=",x["unique_tickers"],
          "MEAN_NET=",x["mean_net_after_2pct"],"LB95=",x["lb95_net_after_2pct"],
          "POS_RATE=",x["positive_net_rate"],"PROFITABLE=",x["profitable_supported"])
print("[RESULT FILE]",RESULT)
if wins:
    print("[RESULT] BTC_NETWORK_SHOCK_KALSHI_NET_EDGE_FOUND")
else:
    print("[RESULT] NO_BTC_NETWORK_SHOCK_KALSHI_NET_EDGE_AFTER_2PCT")
print("[MODEL MUTATION] FALSE")
print("[HURDLE CHANGE] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
