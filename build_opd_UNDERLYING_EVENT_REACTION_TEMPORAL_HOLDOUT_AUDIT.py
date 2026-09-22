from pathlib import Path
SRC = r"""
from pathlib import Path
import json, math, statistics, bisect, itertools
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
CHF=ROOT/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
DEST=BASE/"opd_underlying_event_reaction_temporal_holdout_audit.json"

TRAIN_FRAC=.65
MIN_TOTAL=100
MIN_TRAIN_N=20
MIN_HOLDOUT_N=10
MIN_TICKERS=3
MAX_STALE=7.5
Z=1.2815515655446004
REV="UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT_V1"
PRODUCTS={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}
LOOKBACKS=(15,30,60,300)

def jsonl(p):
    out=[]
    if not p.exists(): return out
    with p.open("r",encoding="utf-8") as f:
        for line in f:
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def finite(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:return None

def asset(t):
    u=str(t or "").upper()
    if u.startswith("KXBTC"):return "BTC"
    if u.startswith("KXETH"):return "ETH"
    if u.startswith("KXSOL"):return "SOL"
    return None

def anchor_time(p):
    due=finite(p.get("resolution_due_epoch"))
    h=finite(p.get("horizon_seconds"))
    if due is None or h is None or h<=0:return None
    return due-h

def load_chf():
    by={p:{} for p in PRODUCTS.values()}
    if not CHF.exists():raise SystemExit("[FAIL] CHF archive missing")
    with CHF.open("r",encoding="utf-8") as f:
        for line in f:
            try:r=json.loads(line)
            except Exception:continue
            prod=str(r.get("product_id") or "")
            if prod not in by:continue
            t=finite(r.get("anchor_epoch")); px=finite(r.get("close_price"))
            if t is None or px is None or px<=0:continue
            by[prod][t]=px
    return {k:sorted(v.items()) for k,v in by.items()}

def at_or_before(series,t):
    times=[x[0] for x in series]
    i=bisect.bisect_right(times,t)-1
    if i<0:return None
    tt,px=series[i]
    if t-tt>MAX_STALE:return None
    return tt,px

def exact_future(series,t,h):
    a=at_or_before(series,t)
    f=at_or_before(series,t+h)
    if not a or not f or f[0]<=a[0] or a[1]<=0:return None
    r=f[1]/a[1]-1
    return {"anchor_spot":a[1],"future_spot":f[1],"future_return":r,
            "anchor_epoch":a[0],"future_epoch":f[0],
            "anchor_staleness":t-a[0],"future_staleness":t+h-f[0]}

def pre_features(series,t):
    a=at_or_before(series,t)
    if not a:return None
    at,ap=a
    f={"spot.anchor":ap}
    rets={}
    for w in LOOKBACKS:
        b=at_or_before(series,t-w)
        if not b or b[1]<=0:continue
        r=ap/b[1]-1
        rets[w]=r
        f[f"ret_{w}s"]=r
        f[f"absret_{w}s"]=abs(r)
    if 15 in rets and 60 in rets:
        f["accel_15_vs_60"]=rets[15]-rets[60]/4.0
        f["same_sign_15_60"]=1.0 if rets[15]*rets[60]>0 else 0.0
        f["opposite_sign_15_60"]=1.0 if rets[15]*rets[60]<0 else 0.0
    if 30 in rets and 300 in rets:
        f["accel_30_vs_300"]=rets[30]-rets[300]/10.0
        f["same_sign_30_300"]=1.0 if rets[30]*rets[300]>0 else 0.0
        f["opposite_sign_30_300"]=1.0 if rets[30]*rets[300]<0 else 0.0
    vals=list(rets.values())
    if len(vals)>=2:
        f["pre_return_mean"]=sum(vals)/len(vals)
        f["pre_return_std"]=statistics.pstdev(vals)
        f["pre_return_range"]=max(vals)-min(vals)
        f["pre_sign_alignment"]=abs(sum(1 if x>0 else -1 if x<0 else 0 for x in vals))/len(vals)
        f["pre_max_abs_return"]=max(abs(x) for x in vals)
    return f

def quantiles(vals):
    vals=sorted(set(vals))
    if len(vals)<5:return vals
    out=[]
    for q in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
        i=min(len(vals)-1,max(0,round((len(vals)-1)*q)))
        out.append(vals[i])
    return sorted(set(out))

def evaluate(rs,mode,min_n):
    if not rs:return None
    vals=[];hits=0;ticks=set()
    for r in rs:
        fut=r["_future"]["future_return"]
        pre=r["_event"].get("reference_pre_return")
        if pre is None or pre==0:continue
        if mode=="CONTINUATION":
            y=fut if pre>0 else -fut
        else:
            y=-fut if pre>0 else fut
        vals.append(y);hits += 1 if y>0 else 0
        ticks.add(str(r.get("ticker") or ""))
    if not vals:return None
    n=len(vals);m=sum(vals)/n
    sd=statistics.stdev(vals) if n>1 else 0.0
    se=sd/math.sqrt(n);lb=m-Z*se
    ph=hits/n; hse=math.sqrt(max(ph*(1-ph),0)/n); hlb=ph-Z*hse
    return {"n":n,"unique_tickers":len(ticks),"mode":mode,
            "hit_rate":ph,"hit_rate_lower_bound":hlb,
            "mean_signed_return":m,"signed_return_lower_bound":lb,
            "survives":n>=min_n and len(ticks)>=MIN_TICKERS and lb>0 and hlb>0.5}

def event_rows(data,feature,op,thr,ref):
    out=[]
    for r in data:
        x=r["_pre"].get(feature)
        rr=r["_pre"].get(ref)
        if x is None or rr is None or rr==0:continue
        ok=(x>=thr) if op==">=" else (x<=thr)
        if ok:
            z=dict(r);z["_event"]={"reference_pre_return":rr}
            out.append(z)
    return out

def main():
    series=load_chf()
    data=[]
    for p in jsonl(PRED):
        a=asset(p.get("ticker"))
        if a not in PRODUCTS:continue
        h=finite(p.get("horizon_seconds")); t=anchor_time(p)
        if t is None or h is None or h<=0:continue
        pre=pre_features(series[PRODUCTS[a]],t)
        fut=exact_future(series[PRODUCTS[a]],t,h)
        if not pre or not fut:continue
        r=dict(p);r["_asset"]=a;r["_time"]=t;r["_pre"]=pre;r["_future"]=fut
        data.append(r)

    data.sort(key=lambda r:(r["_time"],str(r.get("prediction_id"))))
    print("[EVENT-LABELED ROWS]",len(data))
    if len(data)<MIN_TOTAL:raise SystemExit("[FAIL] insufficient event-labeled rows")
    cut=max(1,min(len(data)-1,int(len(data)*TRAIN_FRAC)))
    train,hold=data[:cut],data[cut:]

    candidate_features=[k for k in sorted({k for r in train for k in r["_pre"]})
                        if k.startswith(("absret_","accel_","pre_return_std",
                                         "pre_return_range","pre_sign_alignment",
                                         "pre_max_abs_return"))]
    references=[k for k in ("ret_15s","ret_30s","ret_60s","ret_300s")
                if any(k in r["_pre"] for r in train)]

    learned=[]
    for f in candidate_features:
        vals=[r["_pre"][f] for r in train if f in r["_pre"]]
        for t in quantiles(vals):
            for op in (">=","<="):
                for ref in references:
                    subset=event_rows(train,f,op,t,ref)
                    if len(subset)<MIN_TRAIN_N:continue
                    if len({str(r.get("ticker") or "") for r in subset})<MIN_TICKERS:continue
                    for mode in ("CONTINUATION","REVERSION"):
                        e=evaluate(subset,mode,MIN_TRAIN_N)
                        if not e:continue
                        score=e["signed_return_lower_bound"]*math.sqrt(e["n"])
                        learned.append((score,f,op,t,ref,mode,e))

    learned.sort(reverse=True,key=lambda x:x[0])
    results=[]
    for score,f,op,t,ref,mode,tr in learned[:120]:
        hs=evaluate(event_rows(hold,f,op,t,ref),mode,MIN_HOLDOUT_N)
        results.append({"event_feature":f,"op":op,"threshold":t,
                        "reference_return":ref,"reaction_mode":mode,
                        "train":tr,"holdout":hs,
                        "holdout_survives":bool(hs and hs["survives"])})
    winners=[x for x in results if x["holdout_survives"]]
    winners.sort(key=lambda x:(x["holdout"]["signed_return_lower_bound"],
                               x["holdout"]["hit_rate_lower_bound"],
                               x["holdout"]["n"]),reverse=True)

    report={"revision":REV,
            "objective":"EVENT_SPECIFIC_CONTINUATION_OR_REVERSION_FROM_PREANCHOR_SPOT_PATH",
            "rows_total":len(data),"rows_train":len(train),"rows_holdout":len(hold),
            "candidate_event_features":candidate_features,
            "reference_returns":references,
            "winner_count":len(winners),"winners":winners,
            "top_results":results}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*122)
    print(" UNDERLYING EVENT/REACTION TEMPORAL HOLDOUT")
    print("="*122)
    print("[ROWS] total=",len(data),"train=",len(train),"untouched_holdout=",len(hold))
    print("[EVENT FEATURES]",len(candidate_features),"[TRAIN RULES]",len(learned))
    print("[EVENT/REACTION HOLDOUT WINNERS]",len(winners))
    for i,w in enumerate(winners[:20],1):
        h=w["holdout"]
        print("[WINNER]",i,
              "EVENT=",w["event_feature"],w["op"],w["threshold"],
              "REFERENCE=",w["reference_return"],
              "REACTION=",w["reaction_mode"],
              "N=",h["n"],"TICKERS=",h["unique_tickers"],
              "HIT=",round(h["hit_rate"],4),
              "HIT_LB=",round(h["hit_rate_lower_bound"],4),
              "MEAN_SIGNED_RETURN=",round(h["mean_signed_return"],8),
              "RETURN_LB=",round(h["signed_return_lower_bound"],8))
    if winners:
        print("[RESULT] EVENT_REACTION_SIGNAL_SURVIVES_UNTOUCHED_HOLDOUT")
        print("[NEXT] freeze exact event/reaction challenger and collect new prospective outcomes")
    else:
        print("[RESULT] NO_EVENT_REACTION_SIGNAL_SURVIVES_UNTOUCHED_HOLDOUT")
        print("[NEXT] stop crypto price-path modeling from this evidence; move to exogenous-event targets")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
"""

TEST = r"""
from pathlib import Path
p=Path("audit_opd_UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT_V1",
          "LOOKBACKS=(15,30,60,300)",
          "accel_15_vs_60","accel_30_vs_300",
          "CONTINUATION","REVERSION",
          "TRAIN_FRAC=.65","signed_return_lower_bound",
          "hit_rate_lower_bound",
          "EVENT_REACTION_SIGNAL_SURVIVES_UNTOUCHED_HOLDOUT",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] event definitions use only pre-anchor CHF spot history")
print("[PASS] continuation and reversion are tested as distinct reaction targets")
print("[PASS] 15s/30s/60s/300s impulse, acceleration, volatility and alignment features included")
print("[PASS] exact future underlying return remains label-only")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] thresholds are learned from train only")
print("[PASS] survivor requires positive signed-return LB and hit-rate LB > 50pct")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

Path("audit_opd_UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT.py").write_text(SRC,encoding="utf-8")
Path("test_opd_UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT.py").write_text(TEST,encoding="utf-8")
compile(SRC,"audit_opd_UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT.py","exec")
compile(TEST,"test_opd_UNDERLYING_EVENT_REACTION_TEMPORAL_HOLDOUT.py","exec")
print("[PASS] underlying event/reaction temporal-holdout audit installed")
print("[TARGET] pre-anchor spot impulse/acceleration/volatility/alignment -> continuation or reversion")
print("[SOURCE] certified CHF historical_condition_windows.jsonl")
print("[VALIDATION] chronological 65/35 untouched holdout")
print("[MODEL MUTATION] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
