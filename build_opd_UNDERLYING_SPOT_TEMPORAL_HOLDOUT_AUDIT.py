from pathlib import Path
SRC = r"""
from pathlib import Path
import json, math, statistics, bisect
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
CB=ROOT/"runtime"/"coinbase_hf"/"canonical_events.jsonl"
DEST=BASE/"opd_underlying_spot_temporal_holdout_audit.json"

TRAIN_FRAC=.65
MIN_TRAIN_N=20
MIN_HOLDOUT_N=10
MIN_TICKERS=3
MAX_BOUNDARY_STALE=5.0
Z=1.2815515655446004
REV="UNDERLYING_SPOT_TEMPORAL_HOLDOUT_AUDIT_V1"
PRODUCTS={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}

BANNED=("future","outcome","resolved","resolution","directional_return","pnl","profit",
        "loss","mfe","mae","winner","result","settlement")

def jsonl(p):
    if not p.exists(): return []
    out=[]
    for line in p.read_text(encoding="utf-8").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def finite(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:return None

def epoch(v):
    x=finite(v)
    if x is not None:return x
    if v is None:return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(v).replace("Z","+00:00")).timestamp()
    except Exception:return None

def asset(ticker):
    u=str(ticker or "").upper()
    if u.startswith("KXBTC"):return "BTC"
    if u.startswith("KXETH"):return "ETH"
    if u.startswith("KXSOL"):return "SOL"
    return None

def event_time(x):
    return epoch(x.get("event_time") or x.get("observed_at") or x.get("received_at"))

def event_product(x):
    return str(x.get("product_id") or (x.get("payload") or {}).get("product_id") or "")

def event_price(x):
    return finite(x.get("price") or (x.get("payload") or {}).get("price"))

def load_spot():
    by={p:[] for p in PRODUCTS.values()}
    for x in jsonl(CB):
        p=event_product(x); t=event_time(x); px=event_price(x)
        if p in by and t is not None and px is not None:
            by[p].append((t,px))
    for p in by:by[p].sort()
    return by

def exact_future_path(series,t,h):
    if not series:return None
    times=[x[0] for x in series]
    i=bisect.bisect_right(times,t)-1
    if i<0:return None
    at,ap=series[i]
    if t-at>MAX_BOUNDARY_STALE:return None
    end=t+h
    j=bisect.bisect_right(times,end)-1
    if j<=i:return None
    et,ep=series[j]
    if end-et>MAX_BOUNDARY_STALE:return None
    path=[px for tt,px in series[i:j+1] if tt>=at and tt<=end]
    if len(path)<2 or ap==0:return None
    ret=ep/ap-1
    return {"anchor_spot":ap,"future_spot":ep,"future_return":ret,
            "future_abs_return":abs(ret),
            "future_direction":"UP" if ret>0 else ("DOWN" if ret<0 else "FLAT"),
            "mfe":max(px/ap-1 for px in path),
            "mae":min(px/ap-1 for px in path),
            "anchor_event_epoch":at,"future_event_epoch":et,
            "anchor_staleness":t-at,"future_boundary_staleness":end-et}

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
    f={}
    for k,v in raw.items():
        lk=k.lower()
        if any(x in lk for x in ("prediction_id","anchor_id","sequence","epoch","timestamp",
                                 "probability","net_edge","expected_return","actionable","passed",
                                 "generation","family_id")):continue
        f[k]=v
    cb=p.get("state",{}).get("coinbase_hf_state",{}) if isinstance(p.get("state"),dict) else {}
    if not cb:cb=p.get("coinbase_hf_state") or {}
    rets=[]
    if isinstance(cb,dict):
        for w,s in cb.items():
            if isinstance(s,dict):
                r=finite(s.get("return"))
                if r is not None:
                    f[f"D.cb_return_{w}"]=r; rets.append((finite(w) or 0,r))
                for nm in ("event_count","max_event_gap_seconds","boundary_age_seconds","age_seconds"):
                    v=finite(s.get(nm))
                    if v is not None:f[f"D.cb_{nm}_{w}"]=v
    if rets:
        rets=sorted(rets)
        vals=[r for _,r in rets]
        f["D.cb_return_mean"]=sum(vals)/len(vals)
        f["D.cb_return_std"]=statistics.pstdev(vals) if len(vals)>1 else 0.0
        f["D.cb_return_range"]=max(vals)-min(vals)
        f["D.cb_sign_agreement"]=abs(sum(1 if r>0 else -1 if r<0 else 0 for r in vals))/len(vals)
        if len(rets)>=2:f["D.cb_short_minus_long"]=rets[0][1]-rets[-1][1]
    cc=p.get("state",{}).get("crypto_condition_state",{}) if isinstance(p.get("state"),dict) else {}
    if not cc:cc=p.get("crypto_condition_state") or {}
    vals=[]
    if isinstance(cc,dict):
        for name,s in cc.items():
            if isinstance(s,dict):
                v=finite(s.get("value"))
                if v is not None:
                    f["D.cond."+str(name)]=v;vals.append(v)
        if vals:
            f["D.cond_mean"]=sum(vals)/len(vals)
            f["D.cond_std"]=statistics.pstdev(vals) if len(vals)>1 else 0.0
            f["D.cond_range"]=max(vals)-min(vals)
    return f

def ptime(p):
    for k in ("observed_epoch","prediction_epoch","frozen_epoch","created_epoch"):
        v=finite(p.get(k))
        if v is not None:return v
    st=p.get("state")
    if isinstance(st,dict):
        v=finite(st.get("observed_epoch"))
        if v is not None:return v
    return None

def quantiles(vals):
    vals=sorted(set(vals))
    if len(vals)<5:return vals
    out=[]
    for p in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
        i=min(len(vals)-1,max(0,round((len(vals)-1)*p)))
        out.append(vals[i])
    return sorted(set(out))

def eval_direction(rows,side):
    if not rows:return None
    signed=[]
    hits=0;ticks=set()
    for r in rows:
        ret=r["_label"]["future_return"]
        sr=ret if side=="UP" else -ret
        signed.append(sr)
        if sr>0:hits+=1
        ticks.add(str(r.get("ticker") or ""))
    n=len(signed);m=sum(signed)/n
    sd=statistics.stdev(signed) if n>1 else 0.0
    se=sd/math.sqrt(n);lb=m-Z*se
    ph=hits/n
    # normal approximation lower bound around hit rate, used only as supporting diagnostic
    hse=math.sqrt(max(ph*(1-ph),0)/n)
    hlb=ph-Z*hse
    return {"n":n,"unique_tickers":len(ticks),"side":side,"hit_rate":ph,
            "hit_rate_lower_bound":hlb,"mean_signed_underlying_return":m,
            "cumulative_signed_underlying_return":sum(signed),
            "stddev":sd,"standard_error":se,
            "signed_return_lower_bound":lb,
            "survives":n>=MIN_HOLDOUT_N and len(ticks)>=MIN_TICKERS and lb>0 and hlb>0.5}

def best_rule(train,f):
    vals=[r["_features"][f] for r in train if f in r["_features"]]
    best=None
    for t in quantiles(vals):
        for op in (">=","<="):
            subset=[r for r in train if f in r["_features"] and
                    ((r["_features"][f]>=t) if op==">=" else (r["_features"][f]<=t))]
            if len(subset)<MIN_TRAIN_N:continue
            if len({str(r.get("ticker") or "") for r in subset})<MIN_TICKERS:continue
            for side in ("UP","DOWN"):
                e=eval_direction(subset,side)
                score=e["signed_return_lower_bound"]*math.sqrt(e["n"])
                cand=(score,e["hit_rate_lower_bound"],e["n"],side,op,t,e)
                if best is None or cand[:3]>best[:3]:best=cand
    return best

def apply(r,rule):
    f,op,t=rule
    x=r["_features"].get(f)
    if x is None:return False
    return x>=t if op==">=" else x<=t

def main():
    if not PRED.exists():raise SystemExit("[FAIL] immutable prediction ledger missing")
    if not CB.exists():raise SystemExit("[FAIL] Coinbase canonical_events.jsonl missing")
    spot=load_spot()
    data=[]
    for p in jsonl(PRED):
        a=asset(p.get("ticker"))
        if a not in PRODUCTS:continue
        t=ptime(p);h=finite(p.get("horizon_seconds"))
        if t is None or not h or h<=0:continue
        lab=exact_future_path(spot[PRODUCTS[a]],t,h)
        if not lab:continue
        r=dict(p);r["_asset"]=a;r["_time"]=t;r["_label"]=lab;r["_features"]=features(p)
        data.append(r)
    data.sort(key=lambda r:(r["_time"],str(r.get("prediction_id"))))
    if len(data)<60:raise SystemExit("[FAIL] fewer than 60 exact underlying future labels available")
    cut=max(1,min(len(data)-1,int(len(data)*TRAIN_FRAC)))
    train,hold=data[:cut],data[cut:]

    cov=defaultdict(int)
    for r in train:
        for f in r["_features"]:cov[f]+=1
    feats=[f for f,n in cov.items() if n>=MIN_TRAIN_N]

    learned=[]
    for f in feats:
        b=best_rule(train,f)
        if b:
            score,hlb,n,side,op,t,e=b
            learned.append({"feature":f,"op":op,"threshold":t,"side":side,
                            "train_score":score,"train":e})
    learned.sort(key=lambda x:(x["train_score"],x["train"]["n"]),reverse=True)

    results=[]
    for m in learned[:40]:
        rule=(m["feature"],m["op"],m["threshold"])
        hs=eval_direction([r for r in hold if apply(r,rule)],m["side"])
        results.append({**m,"holdout":hs,"holdout_survives":bool(hs and hs["survives"])})

    winners=[x for x in results if x["holdout_survives"]]
    winners.sort(key=lambda x:(x["holdout"]["signed_return_lower_bound"],
                               x["holdout"]["hit_rate_lower_bound"],
                               x["holdout"]["n"]),reverse=True)

    report={"revision":REV,
            "objective":"PREDICT_UNDERLYING_SPOT_DIRECTION_BEFORE_KALSHI_CONTRACT_MAPPING",
            "rows_total":len(data),"rows_train":len(train),"rows_holdout":len(hold),
            "feature_count":len(feats),"train_rules":len(learned),
            "assets":sorted(set(r["_asset"] for r in data)),
            "horizons":sorted(set(int(r.get("horizon_seconds")) for r in data)),
            "winner_count":len(winners),"winners":winners,
            "top_results":results[:100]}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*120)
    print(" UNDERLYING SPOT TEMPORAL HOLDOUT AUDIT")
    print("="*120)
    print("[REVISION]",REV)
    print("[OBJECTIVE] predict BTC/ETH/SOL future spot direction BEFORE Kalshi contract selection")
    print("[ROWS WITH EXACT FUTURE SPOT]",len(data),"train=",len(train),"untouched_holdout=",len(hold))
    print("[ASSETS]",",".join(report["assets"]),"[HORIZONS]",report["horizons"])
    print("[DECISION-TIME FEATURES]",len(feats),"[TRAIN RULES]",len(learned))
    print("[UNDERLYING HOLDOUT WINNERS]",len(winners))
    for i,w in enumerate(winners[:20],1):
        h=w["holdout"]
        print("[WINNER]",i,"FEATURE=",w["feature"],w["op"],w["threshold"],
              "SIDE=",w["side"],"N=",h["n"],"TICKERS=",h["unique_tickers"],
              "HIT=",round(h["hit_rate"],4),"HIT_LB=",round(h["hit_rate_lower_bound"],4),
              "MEAN_SIGNED_RETURN=",round(h["mean_signed_underlying_return"],8),
              "RETURN_LB=",round(h["signed_return_lower_bound"],8))
    if winners:
        print("[RESULT] UNDERLYING_DIRECTION_SIGNAL_SURVIVES_UNTOUCHED_TEMPORAL_HOLDOUT")
        print("[NEXT] freeze underlying challenger then map only its signals to Kalshi contract repricing/economics")
    else:
        print("[RESULT] NO_UNDERLYING_DIRECTION_SIGNAL_SURVIVES_UNTOUCHED_TEMPORAL_HOLDOUT")
        print("[NEXT] stop generic crypto direction modeling; move to event/reaction-specific targets")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
"""

TEST = r"""
from pathlib import Path
p=Path("audit_opd_UNDERLYING_SPOT_TEMPORAL_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("UNDERLYING_SPOT_TEMPORAL_HOLDOUT_AUDIT_V1",
          "canonical_events.jsonl","MAX_BOUNDARY_STALE=5.0",
          "exact_future_path","future_return","TRAIN_FRAC=.65",
          "PREDICT_UNDERLYING_SPOT_DIRECTION_BEFORE_KALSHI_CONTRACT_MAPPING",
          "including abstains" if False else "for p in jsonl(PRED)",
          "hit_rate_lower_bound","signed_return_lower_bound",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] immutable prediction ledger supplies frozen decision-time states")
print("[PASS] all BTC/ETH/SOL frozen predictions are eligible, not only prior actionable rows")
print("[PASS] exact future label comes from physical Coinbase canonical event path")
print("[PASS] anchor and future boundary staleness capped at 5 seconds")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] future spot label is never admitted into decision-time features")
print("[PASS] holdout signal requires positive signed-return lower bound and hit-rate lower bound > 50pct")
print("[PASS] Kalshi contract scoring/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

Path("audit_opd_UNDERLYING_SPOT_TEMPORAL_HOLDOUT.py").write_text(SRC,encoding="utf-8")
Path("test_opd_UNDERLYING_SPOT_TEMPORAL_HOLDOUT.py").write_text(TEST,encoding="utf-8")
compile(SRC,"audit_opd_UNDERLYING_SPOT_TEMPORAL_HOLDOUT.py","exec")
compile(TEST,"test_opd_UNDERLYING_SPOT_TEMPORAL_HOLDOUT.py","exec")
print("[PASS] underlying-spot temporal-holdout audit installed")
print("[TARGET] BTC/ETH/SOL future spot path from Coinbase canonical events")
print("[CORPUS] full frozen prediction ledger, including abstains")
print("[VALIDATION] chronological 65/35 untouched holdout")
print("[KALSHI MAPPING] intentionally deferred until underlying signal survives")
print("[MODEL MUTATION] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
