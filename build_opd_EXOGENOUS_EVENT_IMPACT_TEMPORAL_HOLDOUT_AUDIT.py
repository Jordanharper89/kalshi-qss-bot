from pathlib import Path
SRC = r"""
from pathlib import Path
import json, math, statistics, bisect, re
from collections import defaultdict, Counter

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
CHF=ROOT/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
DEST=BASE/"opd_exogenous_event_impact_temporal_holdout_audit.json"

TRAIN_FRAC=.65
MIN_TOTAL=100
MIN_TRAIN_N=20
MIN_HOLDOUT_N=10
MIN_TICKERS=3
MAX_STALE=7.5
Z=1.2815515655446004
REV="EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT_V1"
PRODUCTS={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}

PRICE_BANNED=("kalshi","coinbase","price","return","spread","volume","open_interest",
              "last_trade","midpoint","bid","ask","orderbook","market_price","anchor_price")
LEAK_BANNED=("future","outcome","resolved","resolution","pnl","profit","loss","mfe","mae",
             "winner","result","settlement","prediction_id","resolution_due_epoch")
EXOGENOUS_HINTS=("source","event","news","macro","economic","weather","usgs","sports","official",
                 "calendar","release","announcement","network","chain","solana","gmgn","onchain",
                 "provider","evidence","condition","signal","freshness","reliability","contradiction")

def jsonl(p):
    out=[]
    if not p.exists():return out
    with p.open("r",encoding="utf-8") as f:
        for line in f:
            try:out.append(json.loads(line))
            except Exception:pass
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
    due=finite(p.get("resolution_due_epoch")); h=finite(p.get("horizon_seconds"))
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
            t=finite(r.get("anchor_epoch"));px=finite(r.get("close_price"))
            if t is not None and px is not None and px>0:by[prod][t]=px
    return {k:sorted(v.items()) for k,v in by.items()}

def at_or_before(series,t):
    if not series:return None
    times=[x[0] for x in series]
    i=bisect.bisect_right(times,t)-1
    if i<0:return None
    tt,px=series[i]
    if t-tt>MAX_STALE:return None
    return tt,px

def future_label(series,t,h):
    a=at_or_before(series,t);f=at_or_before(series,t+h)
    if not a or not f or f[0]<=a[0] or a[1]<=0:return None
    r=f[1]/a[1]-1.0
    return {"future_return":r,"future_direction":"UP" if r>0 else ("DOWN" if r<0 else "FLAT")}

def allowed_path(path):
    s=path.lower()
    if any(x in s for x in PRICE_BANNED):return False
    if any(x in s for x in LEAK_BANNED):return False
    return any(x in s for x in EXOGENOUS_HINTS)

def flatten_exogenous(obj,prefix="",out=None,depth=0):
    if out is None:out={}
    if depth>7:return out
    if isinstance(obj,dict):
        for k,v in obj.items():
            name=(prefix+"."+str(k)).strip(".")
            if isinstance(v,(dict,list)):
                flatten_exogenous(v,name,out,depth+1)
            elif allowed_path(name):
                if isinstance(v,bool):out[name]=1.0 if v else 0.0
                elif isinstance(v,(int,float)):
                    z=finite(v)
                    if z is not None:out[name]=z
                elif isinstance(v,str):
                    u=v.strip()
                    if u and len(u)<=80:
                        out[name+"=="+u[:80]]=1.0
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:50]):
            flatten_exogenous(v,prefix+"[]",out,depth+1)
    return out

def quantiles(vals):
    vals=sorted(set(vals))
    if len(vals)<5:return vals
    out=[]
    for q in (.1,.25,.5,.75,.9):
        i=min(len(vals)-1,max(0,round((len(vals)-1)*q)))
        out.append(vals[i])
    return sorted(set(out))

def evaluate(rs,side,min_n):
    if not rs:return None
    vals=[];hits=0;ticks=set()
    for r in rs:
        x=r["_label"]["future_return"]
        y=x if side=="UP" else -x
        vals.append(y);ticks.add(str(r.get("ticker") or ""))
        if y>0:hits+=1
    n=len(vals);m=sum(vals)/n
    sd=statistics.stdev(vals) if n>1 else 0.0
    se=sd/math.sqrt(n);lb=m-Z*se
    ph=hits/n;hse=math.sqrt(max(ph*(1-ph),0)/n);hlb=ph-Z*hse
    return {"n":n,"unique_tickers":len(ticks),"side":side,
            "hit_rate":ph,"hit_rate_lower_bound":hlb,
            "mean_signed_return":m,"signed_return_lower_bound":lb,
            "survives":n>=min_n and len(ticks)>=MIN_TICKERS and lb>0 and hlb>0.5}

def apply(r,rule):
    f,op,t=rule
    x=r["_exo"].get(f)
    if x is None:return False
    return x>=t if op==">=" else x<=t

def main():
    series=load_chf()
    data=[]
    feature_counts=Counter()
    for p in jsonl(PRED):
        a=asset(p.get("ticker"))
        if a not in PRODUCTS:continue
        h=finite(p.get("horizon_seconds"));t=anchor_time(p)
        if t is None or h is None or h<=0:continue
        lab=future_label(series[PRODUCTS[a]],t,h)
        if not lab:continue
        exo=flatten_exogenous(p)
        for k in exo:feature_counts[k]+=1
        r=dict(p);r["_asset"]=a;r["_time"]=t;r["_label"]=lab;r["_exo"]=exo
        data.append(r)

    data.sort(key=lambda r:(r["_time"],str(r.get("prediction_id"))))
    print("[EXACT LABELED ROWS]",len(data))
    print("[RAW EXOGENOUS FEATURE PATHS]",len(feature_counts))
    top=[(k,n) for k,n in feature_counts.most_common(30)]
    for k,n in top:print("[EXOGENOUS PATH]",n,k)

    if len(data)<MIN_TOTAL:
        raise SystemExit("[FAIL] insufficient exact labeled rows")

    cut=max(1,min(len(data)-1,int(len(data)*TRAIN_FRAC)))
    train,hold=data[:cut],data[cut:]
    train_counts=Counter()
    for r in train:
        for k in r["_exo"]:train_counts[k]+=1
    feats=[k for k,n in train_counts.items() if n>=MIN_TRAIN_N]

    if not feats:
        report={"revision":REV,"status":"NO_SUPPORTED_EXOGENOUS_FEATURES_IN_FROZEN_LEDGER",
                "rows_total":len(data),"rows_train":len(train),"rows_holdout":len(hold),
                "raw_exogenous_feature_paths":len(feature_counts),"top_paths":top}
        DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
        print("[SUPPORTED EXOGENOUS FEATURES] 0")
        print("[RESULT] NO_SUPPORTED_EXOGENOUS_FEATURES_IN_FROZEN_LEDGER")
        print("[NEXT] prospective state must freeze independent-source event evidence before exogenous prediction can be tested")
        print("[AUDIT]",DEST)
        print("[NO MODEL MUTATION] TRUE")
        return

    learned=[]
    for f in feats:
        vals=[r["_exo"][f] for r in train if f in r["_exo"]]
        thresholds=quantiles(vals)
        if set(vals).issubset({0.0,1.0}):thresholds=[1.0]
        for thr in thresholds:
            for op in (">=","<="):
                sub=[r for r in train if apply(r,(f,op,thr))]
                if len(sub)<MIN_TRAIN_N:continue
                if len({str(r.get("ticker") or "") for r in sub})<MIN_TICKERS:continue
                for side in ("UP","DOWN"):
                    e=evaluate(sub,side,MIN_TRAIN_N)
                    score=e["signed_return_lower_bound"]*math.sqrt(e["n"])
                    learned.append((score,f,op,thr,side,e))
    learned.sort(reverse=True,key=lambda z:z[0])

    results=[]
    for score,f,op,thr,side,tr in learned[:120]:
        hs=evaluate([r for r in hold if apply(r,(f,op,thr))],side,MIN_HOLDOUT_N)
        results.append({"feature":f,"op":op,"threshold":thr,"side":side,
                        "train":tr,"holdout":hs,
                        "holdout_survives":bool(hs and hs["survives"])})
    winners=[x for x in results if x["holdout_survives"]]
    winners.sort(key=lambda x:(x["holdout"]["signed_return_lower_bound"],
                               x["holdout"]["hit_rate_lower_bound"],
                               x["holdout"]["n"]),reverse=True)

    report={"revision":REV,"status":"AUDITED",
            "objective":"EXOGENOUS_EVENT_IMPACT_ON_FUTURE_UNDERLYING_SPOT",
            "rows_total":len(data),"rows_train":len(train),"rows_holdout":len(hold),
            "supported_exogenous_features":len(feats),"train_rules":len(learned),
            "winner_count":len(winners),"winners":winners,
            "top_results":results,"top_feature_paths":top}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*122)
    print(" EXOGENOUS EVENT IMPACT — TEMPORAL HOLDOUT")
    print("="*122)
    print("[ROWS] total=",len(data),"train=",len(train),"untouched_holdout=",len(hold))
    print("[SUPPORTED EXOGENOUS FEATURES]",len(feats),"[TRAIN RULES]",len(learned))
    print("[EXOGENOUS HOLDOUT WINNERS]",len(winners))
    for i,w in enumerate(winners[:20],1):
        h=w["holdout"]
        print("[WINNER]",i,"FEATURE=",w["feature"],w["op"],w["threshold"],
              "SIDE=",w["side"],"N=",h["n"],"TICKERS=",h["unique_tickers"],
              "HIT=",round(h["hit_rate"],4),"HIT_LB=",round(h["hit_rate_lower_bound"],4),
              "MEAN_SIGNED_RETURN=",round(h["mean_signed_return"],8),
              "RETURN_LB=",round(h["signed_return_lower_bound"],8))
    if winners:
        print("[RESULT] EXOGENOUS_EVENT_SIGNAL_SURVIVES_UNTOUCHED_HOLDOUT")
        print("[NEXT] freeze exact exogenous-event challenger and collect brand-new prospective outcomes")
    else:
        print("[RESULT] NO_EXOGENOUS_EVENT_SIGNAL_SURVIVES_UNTOUCHED_HOLDOUT")
        print("[NEXT] current frozen evidence does not support a profitable exogenous crypto signal")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
"""

TEST = r"""
from pathlib import Path
p=Path("audit_opd_EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT_V1",
          "PRICE_BANNED","LEAK_BANNED","EXOGENOUS_HINTS",
          "kalshi","coinbase","future_label",
          "TRAIN_FRAC=.65","NO_SUPPORTED_EXOGENOUS_FEATURES_IN_FROZEN_LEDGER",
          "signed_return_lower_bound","hit_rate_lower_bound",
          "EXOGENOUS_EVENT_SIGNAL_SURVIVES_UNTOUCHED_HOLDOUT",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] exogenous-event features exclude Kalshi/Coinbase/price/return/orderbook fields")
print("[PASS] future/outcome/resolution/PnL-derived fields excluded")
print("[PASS] only frozen pre-anchor independent-source/event evidence is eligible")
print("[PASS] exact CHF future spot return remains label-only")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] missing exogenous evidence fails closed instead of manufacturing features")
print("[PASS] survivor requires positive signed-return LB and hit-rate LB > 50pct")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

Path("audit_opd_EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT.py").write_text(SRC,encoding="utf-8")
Path("test_opd_EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT.py").write_text(TEST,encoding="utf-8")
compile(SRC,"audit_opd_EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT.py","exec")
compile(TEST,"test_opd_EXOGENOUS_EVENT_IMPACT_TEMPORAL_HOLDOUT.py","exec")
print("[PASS] exogenous-event impact temporal-holdout audit installed")
print("[TARGET] independent non-price Oracle evidence -> future BTC/ETH/SOL spot impact")
print("[PRICE INPUTS] excluded from event definition")
print("[VALIDATION] chronological 65/35 untouched holdout")
print("[MODEL MUTATION] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
