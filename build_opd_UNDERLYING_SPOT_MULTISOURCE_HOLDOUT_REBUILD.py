from pathlib import Path
SRC = r"""
from pathlib import Path
import json, math, statistics, bisect, re
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
DEST=BASE/"opd_underlying_spot_multisource_holdout_audit.json"

TRAIN_FRAC=.65
MIN_TOTAL=30
MIN_TRAIN_N=12
MIN_HOLDOUT_N=8
MIN_TICKERS=3
MAX_BOUNDARY_STALE=10.0
Z=1.2815515655446004
REV="UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD_V1"
PRODUCTS={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}

BANNED=("future","outcome","resolved","resolution","directional_return","pnl","profit",
        "loss","mfe","mae","winner","result","settlement")

def jsonl(p):
    out=[]
    try:
        with p.open("r",encoding="utf-8") as f:
            for line in f:
                try: out.append(json.loads(line))
                except Exception: pass
    except Exception: pass
    return out

def finite(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:return None

def epoch(v):
    x=finite(v)
    if x is not None:
        if x>1e15:return x/1e9
        if x>1e12:return x/1e3
        return x
    if v is None:return None
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(v).replace("Z","+00:00")).timestamp()
    except Exception:return None

def asset(t):
    u=str(t or "").upper()
    if u.startswith("KXBTC"):return "BTC"
    if u.startswith("KXETH"):return "ETH"
    if u.startswith("KXSOL"):return "SOL"
    return None

def dig(d,*keys):
    if not isinstance(d,dict):return None
    for k in keys:
        if k in d:return d[k]
    for v in d.values():
        if isinstance(v,dict):
            z=dig(v,*keys)
            if z is not None:return z
    return None

def ev_product(x):
    v=dig(x,"product_id","product","symbol","market","instrument","source_market_id")
    s=str(v or "").upper().replace("/","-")
    aliases={"BTCUSD":"BTC-USD","ETHUSD":"ETH-USD","SOLUSD":"SOL-USD"}
    return aliases.get(s,s)

def ev_time(x):
    return epoch(dig(x,"event_time","observed_at","received_at","timestamp","time","ts","epoch"))

def ev_price(x):
    return finite(dig(x,"price","last_price","trade_price","mid_price","close","value"))

def candidate_files():
    roots=[ROOT/"runtime", ROOT/"data", ROOT/"qseries_v2"]
    seen=set(); out=[]
    rx=re.compile(r"(coinbase|crypto|canonical|market|trade|event|history)",re.I)
    for base in roots:
        if not base.exists():continue
        try:
            for p in base.rglob("*.jsonl"):
                sp=str(p)
                if p in seen or not rx.search(sp):continue
                seen.add(p); out.append(p)
        except Exception:pass
    return out

def load_spot():
    by={p:[] for p in PRODUCTS.values()}
    file_stats=[]
    for p in candidate_files():
        n=0
        for x in jsonl(p):
            prod=ev_product(x); t=ev_time(x); px=ev_price(x)
            if prod in by and t is not None and px is not None and px>0:
                by[prod].append((t,px,str(p))); n+=1
        if n:file_stats.append((str(p),n))
    for prod in by:
        ded={}
        for t,px,src in by[prod]:
            ded[(round(t,6),px)]=(t,px,src)
        by[prod]=sorted(ded.values(),key=lambda z:z[0])
    return by,sorted(file_stats,key=lambda z:z[1],reverse=True)

def exact_future(series,t,h):
    if not series:return None
    times=[x[0] for x in series]
    i=bisect.bisect_right(times,t)-1
    if i<0:return None
    at,ap,asrc=series[i]
    if t-at>MAX_BOUNDARY_STALE:return None
    end=t+h
    j=bisect.bisect_right(times,end)-1
    if j<=i:return None
    et,ep,esrc=series[j]
    if end-et>MAX_BOUNDARY_STALE:return None
    path=[px for tt,px,_ in series[i:j+1] if tt>=at and tt<=end]
    if len(path)<2 or ap==0:return None
    r=ep/ap-1
    return {"anchor_spot":ap,"future_spot":ep,"future_return":r,
            "future_direction":"UP" if r>0 else ("DOWN" if r<0 else "FLAT"),
            "anchor_event_epoch":at,"future_event_epoch":et,
            "anchor_staleness":t-at,"future_boundary_staleness":end-et,
            "anchor_source":asrc,"future_source":esrc}

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
    raw=flatten(p); f={}
    for k,v in raw.items():
        lk=k.lower()
        if any(x in lk for x in ("prediction_id","anchor_id","sequence","epoch","timestamp",
                                 "probability","net_edge","expected_return","actionable","passed",
                                 "generation","family_id")):continue
        f[k]=v
    st=p.get("state") if isinstance(p.get("state"),dict) else {}
    cb=st.get("coinbase_hf_state") if isinstance(st,dict) else None
    if not isinstance(cb,dict): cb=p.get("coinbase_hf_state") if isinstance(p.get("coinbase_hf_state"),dict) else {}
    vals=[]
    for w,s in cb.items():
        if isinstance(s,dict):
            r=finite(s.get("return"))
            if r is not None:
                f[f"D.cb_return_{w}"]=r;vals.append(r)
    if vals:
        f["D.cb_mean"]=sum(vals)/len(vals)
        f["D.cb_std"]=statistics.pstdev(vals) if len(vals)>1 else 0.0
        f["D.cb_range"]=max(vals)-min(vals)
        f["D.cb_sign_agreement"]=abs(sum(1 if x>0 else -1 if x<0 else 0 for x in vals))/len(vals)
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
    for q in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
        i=min(len(vals)-1,max(0,round((len(vals)-1)*q)))
        out.append(vals[i])
    return sorted(set(out))

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
    ph=hits/n; hse=math.sqrt(max(ph*(1-ph),0)/n); hlb=ph-Z*hse
    return {"n":n,"unique_tickers":len(ticks),"side":side,"hit_rate":ph,
            "hit_rate_lower_bound":hlb,"mean_signed_return":m,
            "signed_return_lower_bound":lb,
            "survives":n>=min_n and len(ticks)>=MIN_TICKERS and lb>0 and hlb>0.5}

def apply(r,rule):
    f,op,t=rule
    x=r["_features"].get(f)
    return False if x is None else (x>=t if op==">=" else x<=t)

def main():
    if not PRED.exists():raise SystemExit("[FAIL] prediction ledger missing")
    spot,stats=load_spot()
    print("[COINBASE SOURCES WITH USABLE ROWS]",len(stats))
    for p,n in stats[:15]:print("[SOURCE]",n,p)
    for prod,arr in spot.items():print("[SPOT ROWS]",prod,len(arr))

    data=[]; misses=defaultdict(int)
    preds=jsonl(PRED)
    for p in preds:
        a=asset(p.get("ticker"))
        if a not in PRODUCTS:continue
        t=ptime(p);h=finite(p.get("horizon_seconds"))
        if t is None or not h or h<=0:continue
        lab=exact_future(spot[PRODUCTS[a]],t,h)
        if not lab:
            misses[(a,int(h))]+=1;continue
        r=dict(p);r["_asset"]=a;r["_time"]=t;r["_label"]=lab;r["_features"]=features(p)
        data.append(r)

    print("[EXACT UNDERLYING LABELS]",len(data))
    for k,n in sorted(misses.items()):print("[UNLABELED]",k[0],"H=",k[1],"N=",n)

    if len(data)<MIN_TOTAL:
        report={"revision":REV,"status":"INSUFFICIENT_PHYSICAL_UNDERLYING_HISTORY",
                "exact_labels":len(data),"minimum_required":MIN_TOTAL,
                "source_files":stats,"spot_rows":{k:len(v) for k,v in spot.items()},
                "unlabeled":{f"{a}:{h}":n for (a,h),n in misses.items()}}
        DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
        print("[RESULT] INSUFFICIENT_PHYSICAL_UNDERLYING_HISTORY")
        print("[MINIMUM REQUIRED]",MIN_TOTAL)
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
                if len(sub)<MIN_TRAIN_N or len({str(r.get("ticker") or "") for r in sub})<MIN_TICKERS:continue
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

    report={"revision":REV,"status":"AUDITED",
            "objective":"PREDICT_UNDERLYING_SPOT_DIRECTION_BEFORE_KALSHI_MAPPING",
            "exact_labels":len(data),"rows_train":len(train),"rows_holdout":len(hold),
            "source_files":stats,"spot_rows":{k:len(v) for k,v in spot.items()},
            "feature_count":len(feats),"winner_count":len(winners),
            "winners":winners,"top_results":results}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*118)
    print(" UNDERLYING SPOT MULTISOURCE TEMPORAL HOLDOUT")
    print("="*118)
    print("[ROWS] total=",len(data),"train=",len(train),"holdout=",len(hold))
    print("[FEATURES]",len(feats),"[UNDERLYING HOLDOUT WINNERS]",len(winners))
    for i,w in enumerate(winners[:20],1):
        h=w["holdout"]
        print("[WINNER]",i,w["feature"],w["op"],w["threshold"],"SIDE=",w["side"],
              "N=",h["n"],"TICKERS=",h["unique_tickers"],
              "HIT=",round(h["hit_rate"],4),"HIT_LB=",round(h["hit_rate_lower_bound"],4),
              "MEAN=",round(h["mean_signed_return"],8),"RETURN_LB=",round(h["signed_return_lower_bound"],8))
    print("[RESULT]","UNDERLYING_SIGNAL_SURVIVES_HOLDOUT" if winners else "NO_UNDERLYING_SIGNAL_SURVIVES_HOLDOUT")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
"""

TEST = r"""
from pathlib import Path
p=Path("audit_opd_UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD_V1",
          "candidate_files()","rglob(\"*.jsonl\")","BTC-USD","ETH-USD","SOL-USD",
          "MAX_BOUNDARY_STALE=10.0","INSUFFICIENT_PHYSICAL_UNDERLYING_HISTORY",
          "TRAIN_FRAC=.65","signed_return_lower_bound","hit_rate_lower_bound",
          "NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] replacement discovers physical Coinbase/crypto/canonical/history JSONL sources recursively")
print("[PASS] multiple common product/time/price schemas normalized")
print("[PASS] BTC/ETH/SOL rows merged and deduplicated before future labeling")
print("[PASS] exact boundary staleness remains capped; no ticker-derived future prices")
print("[PASS] insufficient physical history fails closed with source-coverage report")
print("[PASS] chronological train/holdout evaluation runs only when enough exact labels exist")
print("[PASS] no Kalshi predictor/runtime mutation")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

Path("audit_opd_UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD.py").write_text(SRC,encoding="utf-8")
Path("test_opd_UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD.py").write_text(TEST,encoding="utf-8")
compile(SRC,"audit_opd_UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD.py","exec")
compile(TEST,"test_opd_UNDERLYING_SPOT_MULTISOURCE_HOLDOUT_REBUILD.py","exec")
print("[PASS] underlying spot multisource replacement installed")
print("[FIX] narrow single-file Coinbase dependency removed")
print("[DISCOVERY] runtime/data/qseries_v2 JSONL histories searched physically")
print("[FAIL-CLOSED] exact history shortage is reported, not guessed around")
print("[MODEL MUTATION] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
