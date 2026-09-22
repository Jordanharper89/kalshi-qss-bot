
from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime"/"predictive_data"/"opd_btc_network_shock_underlying_holdout_audit_v1.json"
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
CHF=ROOT/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
RESULT=ROOT/"runtime"/"predictive_data"/"opd_btc_network_shock_incremental_alpha_audit_v1.json"

TRAIN_FRAC=0.65
MIN_HOLDOUT_N=12
MIN_TICKERS=3
HORIZONS={5,15,30,60}

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

def lb95(xs):
    if not xs:return None
    mu=sum(xs)/len(xs)
    if len(xs)==1:return mu
    return mu-1.96*(statistics.stdev(xs)/math.sqrt(len(xs)))

def prediction_time(p):
    for k in ("prediction_epoch","frozen_epoch","created_epoch","anchor_observed_epoch","observed_epoch"):
        v=flt(p.get(k))
        if v is not None:return v
    due=flt(p.get("resolution_due_epoch")); h=flt(p.get("horizon_seconds"))
    return due-h if due is not None and h is not None else None

# Reconstruct unique decision anchors used by the discovery audit.
anchors=[]
seen=set()
for p in load_jsonl(PRED):
    if str(p.get("asset") or "").upper()!="BTC": continue
    h=int(p.get("horizon_seconds") or 0)
    if h not in HORIZONS: continue
    t=prediction_time(p)
    if t is None: continue
    k=(round(t,3),h,str(p.get("ticker") or ""))
    if k in seen: continue
    seen.add(k)
    anchors.append({"time":t,"h":h,"ticker":str(p.get("ticker") or "")})
anchors.sort(key=lambda x:(x["time"],x["h"],x["ticker"]))

labels={}
for r in load_jsonl(CHF):
    if str(r.get("product_id") or "").upper()!="BTC-USD": continue
    h=int(r.get("window_seconds") or 0)
    if h not in HORIZONS or not r.get("full_horizon_complete"): continue
    a=flt(r.get("anchor_epoch")); ret=flt(r.get("return"))
    if a is not None and ret is not None: labels[(round(a,3),h)]=ret

rows=[]
for a in anchors:
    ret=labels.get((round(a["time"],3),a["h"]))
    if ret is None:
        base=round(a["time"]/5.0)*5.0
        c=[]
        for x in (base-5.0,base,base+5.0):
            r=labels.get((round(x,3),a["h"]))
            if r is not None and abs(x-a["time"])<=2.5:c.append((abs(x-a["time"]),r))
        if c: ret=min(c,key=lambda z:z[0])[1]
    if ret is not None:
        rows.append({**a,"future_spot_return":ret})

rows.sort(key=lambda x:(x["time"],x["h"],x["ticker"]))
cut=max(1,min(len(rows)-1,int(len(rows)*TRAIN_FRAC))) if len(rows)>=2 else len(rows)
hold=rows[cut:]

src=json.loads(SRC.read_text(encoding="utf-8"))
winners=src.get("winners") or []

out=[]
for w in winners:
    h=int(w["horizon_seconds"])
    d=str(w["direction"]).upper()
    base=[r for r in hold if r["h"]==h]
    if len(base)<MIN_HOLDOUT_N: continue
    vals=[(r["future_spot_return"] if d=="UP" else -r["future_spot_return"]) for r in base]
    base_mu=sum(vals)/len(vals)
    signal_mu=float(w["holdout_mean_directional_spot_return"])
    alpha=signal_mu-base_mu

    # Conservative paired-style uncertainty proxy: compare signal mean against
    # full same-horizon/direction holdout baseline with pooled standard error.
    sig_n=int(w["holdout_n"])
    base_sd=statistics.stdev(vals) if len(vals)>1 else 0.0
    se=base_sd/math.sqrt(max(1,sig_n)) + base_sd/math.sqrt(max(1,len(vals)))
    alpha_lb=alpha-1.96*se

    out.append({
        **w,
        "baseline_holdout_n":len(base),
        "baseline_mean_directional_spot_return":base_mu,
        "incremental_alpha_vs_same_horizon_direction":alpha,
        "incremental_alpha_lb95_proxy":alpha_lb,
        "incremental_alpha_positive":alpha_lb>0,
    })

out.sort(key=lambda x:(x["incremental_alpha_positive"],x["incremental_alpha_lb95_proxy"]),reverse=True)
survivors=[x for x in out if x["incremental_alpha_positive"]]

payload={
"revision":"BTC_NETWORK_SHOCK_INCREMENTAL_ALPHA_AUDIT_V1",
"discovery_winners":len(winners),
"evaluated_winners":len(out),
"incremental_alpha_survivors":len(survivors),
"survivors":survivors[:100],
"all_results":out[:200],
}
RESULT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

print("[DISCOVERY WINNERS]",len(winners))
print("[INCREMENTAL ALPHA SURVIVORS]",len(survivors))
for x in out[:30]:
    print("[ALPHA] H=",x["horizon_seconds"],"FEATURE=",x["feature"],"OP=",x["op"],"TH=",x["threshold"],
          "DIR=",x["direction"],"SIG_N=",x["holdout_n"],
          "SIG_RET=",x["holdout_mean_directional_spot_return"],
          "BASE_RET=",x["baseline_mean_directional_spot_return"],
          "ALPHA=",x["incremental_alpha_vs_same_horizon_direction"],
          "ALPHA_LB95=",x["incremental_alpha_lb95_proxy"],
          "SURVIVES=",x["incremental_alpha_positive"])
print("[RESULT FILE]",RESULT)
if survivors:
    print("[RESULT] NETWORK_SHOCK_INCREMENTAL_ALPHA_SURVIVES_DRIFT_CONTROL")
else:
    print("[RESULT] NETWORK_SHOCK_WINNERS_EXPLAINED_BY_BASELINE_DRIFT")
print("[MODEL MUTATION] FALSE")
print("[KALSHI MAPPING] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
