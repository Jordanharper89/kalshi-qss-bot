
from pathlib import Path
import json, math, statistics, bisect
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
CHF=ROOT/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
DEST=BASE/"opd_underlying_spot_chf_history_holdout_audit.json"

TRAIN_FRAC=.65
MIN_TOTAL=30
MIN_TRAIN_N=12
MIN_HOLDOUT_N=8
MIN_TICKERS=3
MAX_BOUNDARY_STALE=7.5
Z=1.2815515655446004
REV="UNDERLYING_SPOT_CHF_HISTORY_HOLDOUT_V1"
PRODUCTS={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}

BANNED=("future","outcome","resolved","resolution","directional_return","pnl","profit",
        "loss","mfe","mae","winner","result","settlement")

def jsonl(p):
    if not p.exists(): return []
    out=[]
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

def prediction_time(p):
    for k in ("observed_epoch","prediction_epoch","frozen_epoch","created_epoch"):
        v=finite(p.get(k))
        if v is not None:return v
    st=p.get("state")
    if isinstance(st,dict):
        v=finite(st.get("observed_epoch"))
        if v is not None:return v
    return None

def load_chf():
    by={p:{} for p in PRODUCTS.values()}
    total=0
    if not CHF.exists():
        raise SystemExit("[FAIL] CHF historical archive missing: "+str(CHF))
    with CHF.open("r",encoding="utf-8") as f:
        for line in f:
            try:r=json.loads(line)
            except Exception:continue
            prod=str(r.get("product_id") or "")
            if prod not in by:continue
            t=finite(r.get("anchor_epoch"))
            px=finite(r.get("close_price"))
            if t is None or px is None or px<=0:continue
            # CHF-016 writes one row per lookback horizon at each 5s anchor.
            # close_price is the same anchor spot; dedupe on anchor_epoch.
            by[prod][t]=px
            total+=1
    series={}
    for prod,d in by.items():
        series[prod]=sorted(d.items())
    return series,total

def exact_label(series,t,h):
    if not series:return None
    times=[x[0] for x in series]
    ia=bisect.bisect_right(times,t)-1
    if ia<0:return None
    at,ap=series[ia]
    if t-at>MAX_BOUNDARY_STALE:return None
    target=t+h
    jf=bisect.bisect_right(times,target)-1
    if jf<=ia:return None
    ft,fp=series[jf]
    if target-ft>MAX_BOUNDARY_STALE:return None
    if ap<=0:return None
    r=fp/ap-1.0
    return {"anchor_spot":ap,"future_spot":fp,"future_return":r,
            "future_direction":"UP" if r>0 else ("DOWN" if r<0 else "FLAT"),
            "anchor_epoch":at,"future_epoch":ft,
            "anchor_staleness":t-at,"future_staleness":target-ft}

def flatten(obj,prefix="",out=None,depth=0):
    if out is None:out={}
    if depth>6:return out
    if isinstance(obj,dict):
        for k,v in obj.items():
            name=(prefix+"."+str(k)).strip(".")
            if any(b in name.lower() for b in BANNED):continue
            flatten(v,name,out,depth+1)
    elif isinstance(obj,bool):out[prefix]=1.0 if obj else 0.0
    elif isinstance(obj,(int,float)):
        v=finite(obj)
        if v is not None:out[prefix]=v
    return out

def features(p):
    raw=flatten(p)
    out={}
    for k,v in raw.items():
        lk=k.lower()
        if any(x in lk for x in ("prediction_id","anchor_id","sequence","epoch","timestamp",
                                 "probability","net_edge","expected_return","actionable","passed",
                                 "generation","family_id")):
            continue
        out[k]=v
    st=p.get("state") if isinstance(p.get("state"),dict) else {}
    cb=st.get("coinbase_hf_state") if isinstance(st,dict) else None
    if not isinstance(cb,dict):
        cb=p.get("coinbase_hf_state") if isinstance(p.get("coinbase_hf_state"),dict) else {}
    vals=[]
    for w,s in cb.items():
        if isinstance(s,dict):
            rr=finite(s.get("return"))
            if rr is not None:
                out[f"D.cb_return_{w}"]=rr
                vals.append(rr)
    if vals:
        out["D.cb_return_mean"]=sum(vals)/len(vals)
        out["D.cb_return_std"]=statistics.pstdev(vals) if len(vals)>1 else 0.0
        out["D.cb_return_range"]=max(vals)-min(vals)
        out["D.cb_sign_agreement"]=abs(sum(1 if x>0 else -1 if x<0 else 0 for x in vals))/len(vals)
    return out

def quantiles(vals):
    vals=sorted(set(vals))
    if len(vals)<5:return vals
    q=[]
    for p in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
        i=min(len(vals)-1,max(0,round((len(vals)-1)*p)))
        q.append(vals[i])
    return sorted(set(q))

def evaluate(rs,side,min_n):
    if not rs:return None
    signed=[];ticks=set();hits=0
    for r in rs:
        x=r["_label"]["future_return"]
        y=x if side=="UP" else -x
        signed.append(y);ticks.add(str(r.get("ticker") or ""))
        if y>0:hits+=1
    n=len(signed);m=sum(signed)/n
    sd=statistics.stdev(signed) if n>1 else 0.0
    se=sd/math.sqrt(n);lb=m-Z*se
    ph=hits/n
    hse=math.sqrt(max(ph*(1-ph),0)/n)
    hlb=ph-Z*hse
    return {"n":n,"unique_tickers":len(ticks),"side":side,
            "hit_rate":ph,"hit_rate_lower_bound":hlb,
            "mean_signed_return":m,"cumulative_signed_return":sum(signed),
            "signed_return_lower_bound":lb,
            "survives":n>=min_n and len(ticks)>=MIN_TICKERS and lb>0 and hlb>0.5}

def apply(r,rule):
    f,op,t=rule
    x=r["_features"].get(f)
    if x is None:return False
    return x>=t if op==">=" else x<=t

def main():
    if not PRED.exists():raise SystemExit("[FAIL] prediction ledger missing")
    series,raw_rows=load_chf()
    print("[CHF ARCHIVE]",CHF)
    print("[CHF RAW ROWS READ]",raw_rows)
    for prod,arr in series.items():
        span=((arr[-1][0]-arr[0][0])/60.0) if len(arr)>1 else 0.0
        print("[CHF SPOT ANCHORS]",prod,len(arr),"SPAN_MINUTES=",round(span,3))

    data=[];unlabeled=defaultdict(int)
    preds=jsonl(PRED)
    for p in preds:
        a=asset(p.get("ticker"))
        if a not in PRODUCTS:continue
        t=prediction_time(p);h=finite(p.get("horizon_seconds"))
        if t is None or not h or h<=0:continue
        lab=exact_label(series[PRODUCTS[a]],t,h)
        if not lab:
            unlabeled[(a,int(h))]+=1
            continue
        r=dict(p);r["_asset"]=a;r["_time"]=t;r["_label"]=lab;r["_features"]=features(p)
        data.append(r)

    print("[EXACT UNDERLYING LABELS]",len(data))
    for (a,h),n in sorted(unlabeled.items()):
        print("[UNLABELED]",a,"H=",h,"N=",n)

    if len(data)<MIN_TOTAL:
        report={"revision":REV,"status":"INSUFFICIENT_CHF_HISTORY_FOR_CURRENT_PREDICTION_EPOCHS",
                "exact_labels":len(data),"minimum_required":MIN_TOTAL,
                "spot_anchor_counts":{k:len(v) for k,v in series.items()},
                "unlabeled":{f"{a}:{h}":n for (a,h),n in unlabeled.items()}}
        DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
        print("[RESULT] INSUFFICIENT_CHF_HISTORY_FOR_CURRENT_PREDICTION_EPOCHS")
        print("[AUDIT]",DEST)
        print("[NO MODEL MUTATION] TRUE")
        return

    data.sort(key=lambda r:(r["_time"],str(r.get("prediction_id"))))
    cut=max(1,min(len(data)-1,int(len(data)*TRAIN_FRAC)))
    train,hold=data[:cut],data[cut:]

    cov=defaultdict(int)
    for r in train:
        for f in r["_features"]:cov[f]+=1
    feats=[f for f,n in cov.items() if n>=MIN_TRAIN_N]

    learned=[]
    for f in feats:
        vals=[r["_features"][f] for r in train if f in r["_features"]]
        for t in quantiles(vals):
            for op in (">=","<="):
                sub=[r for r in train if apply(r,(f,op,t))]
                if len(sub)<MIN_TRAIN_N:continue
                if len({str(r.get("ticker") or "") for r in sub})<MIN_TICKERS:continue
                for side in ("UP","DOWN"):
                    e=evaluate(sub,side,MIN_TRAIN_N)
                    score=e["signed_return_lower_bound"]*math.sqrt(e["n"])
                    learned.append((score,f,op,t,side,e))
    learned.sort(reverse=True,key=lambda z:z[0])

    results=[]
    for score,f,op,t,side,tr in learned[:60]:
        hs=evaluate([r for r in hold if apply(r,(f,op,t))],side,MIN_HOLDOUT_N)
        results.append({"feature":f,"op":op,"threshold":t,"side":side,
                        "train":tr,"holdout":hs,
                        "holdout_survives":bool(hs and hs["survives"])})
    winners=[x for x in results if x["holdout_survives"]]
    winners.sort(key=lambda x:(x["holdout"]["signed_return_lower_bound"],
                               x["holdout"]["hit_rate_lower_bound"],
                               x["holdout"]["n"]),reverse=True)

    report={"revision":REV,"status":"AUDITED",
            "objective":"PREDICT_UNDERLYING_SPOT_DIRECTION_FROM_FROZEN_ORACLE_STATE",
            "exact_labels":len(data),"rows_train":len(train),"rows_holdout":len(hold),
            "feature_count":len(feats),"winner_count":len(winners),
            "winners":winners,"top_results":results}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*120)
    print(" UNDERLYING SPOT — CHF HISTORICAL ARCHIVE TEMPORAL HOLDOUT")
    print("="*120)
    print("[ROWS] total=",len(data),"train=",len(train),"untouched_holdout=",len(hold))
    print("[FEATURES]",len(feats),"[UNDERLYING HOLDOUT WINNERS]",len(winners))
    for i,w in enumerate(winners[:20],1):
        h=w["holdout"]
        print("[WINNER]",i,"FEATURE=",w["feature"],w["op"],w["threshold"],
              "SIDE=",w["side"],"N=",h["n"],"TICKERS=",h["unique_tickers"],
              "HIT=",round(h["hit_rate"],4),"HIT_LB=",round(h["hit_rate_lower_bound"],4),
              "MEAN_SIGNED_RETURN=",round(h["mean_signed_return"],8),
              "RETURN_LB=",round(h["signed_return_lower_bound"],8))
    print("[RESULT]","UNDERLYING_SIGNAL_SURVIVES_HOLDOUT" if winners else "NO_UNDERLYING_SIGNAL_SURVIVES_HOLDOUT")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
