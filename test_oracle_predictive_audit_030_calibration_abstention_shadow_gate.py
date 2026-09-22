from collections import defaultdict
from bisect import bisect_right
from datetime import timedelta
import json,re,math,statistics
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
TICKER_RE=re.compile(r"\bKXBTC15M-[A-Z0-9-]+\b",re.I)
RAW_PREFIXES=("source.crypto.condition.btc.coinbase.","source.crypto.condition.btc.bitcoin.")
PRICE_KEYS=("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")
BID_KEYS=("yes_bid_dollars",); ASK_KEYS=("yes_ask_dollars",)

def walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            yield str(k),v
            yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def asdict(obj):
    try: return obj if isinstance(obj,dict) else json.loads(obj)
    except Exception: return {}

def numeric_map(obj):
    d=asdict(obj); z={}
    for k,v in walk(d):
        try:
            f=float(v)
            if math.isfinite(f): z.setdefault(k.lower(),f)
        except Exception: pass
    return z

def kalshi_parse(obj):
    d=asdict(obj)
    text=json.dumps(d,default=str).upper(); m=TICKER_RE.search(text)
    if not m: return None,None,None
    vals=numeric_map(d)
    p=None
    for k in PRICE_KEYS[:3]:
        v=vals.get(k)
        if v is not None and 0<=v<=1: p=v; break
    bid=vals.get("yes_bid_dollars"); ask=vals.get("yes_ask_dollars")
    if p is None and bid is not None and ask is not None and 0<=bid<=ask<=1: p=(bid+ask)/2
    spread=(ask-bid) if bid is not None and ask is not None and 0<=bid<=ask<=1 else None
    return m.group(0),p,spread

def load_rows():
    rows=[]; cursor=None
    for page in range(1,5):
        with connect(ROOT,autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute("SET LOCAL statement_timeout='15000ms'")
                sql="SELECT sequence_number,observed_at,source_id,canonical_observation_json FROM public.oracle_canonical_observations"
                args=[]
                if cursor is not None:
                    sql+=" WHERE sequence_number < %s"; args.append(cursor)
                sql+=" ORDER BY sequence_number DESC LIMIT 50000"
                q.execute(sql,tuple(args)); b=q.fetchall() or []
            c.rollback()
        print("[PAGE]",page,"rows=",len(b))
        if not b: break
        rows+=b; cursor=min(int(x[0]) for x in b)
    return rows

def scalar_value(obj, source):
    vals=numeric_map(obj)
    hints=("spot_price","price","value","bid_ask_spread_bps","spot_volume_24h","mempool_transaction_count",
           "mempool_vsize","fastest_fee_rate","half_hour_fee_rate","tip_block_size","tip_block_tx_count","tip_block_weight")
    tail=source.rsplit(".",1)[-1].lower()
    for k in (tail,)+hints:
        if k in vals: return vals[k]
    # conservative fallback: only when exactly one numeric leaf exists
    uniq=list(vals.values())
    return uniq[0] if len(uniq)==1 else None

def build_data(rows):
    paths=defaultdict(list); raw=defaultdict(list)
    for seq,ts,source,obj in rows:
        if ts is None: continue
        s=str(source)
        if s=="source.kalshi.market_data":
            t,p,sp=kalshi_parse(obj)
            if t and p is not None: paths[t].append((ts,int(seq),float(p),sp))
        elif s.startswith(RAW_PREFIXES):
            v=scalar_value(obj,s)
            raw[s].append((ts,int(seq),v))
    for t in paths: paths[t].sort(key=lambda x:(x[0],x[1]))
    for s in raw: raw[s].sort(key=lambda x:(x[0],x[1]))
    return paths,raw

def raw_features(raw, ts):
    f={}; fresh=[]
    for s,arr in raw.items():
        times=[x[0] for x in arr]; i=bisect_right(times,ts)-1
        if i<0: continue
        lag=(ts-arr[i][0]).total_seconds()
        if not (0<=lag<=60): continue
        fresh.append(lag); cur=arr[i][2]
        prev=None
        j=i-1
        while j>=0 and (ts-arr[j][0]).total_seconds()<=300:
            if arr[j][2] is not None and cur is not None:
                prev=arr[j]; break
            j-=1
        key=s.rsplit(".",1)[-1]
        f["raw_"+key+"_present"]=1.0
        f["raw_"+key+"_lag"]=lag/60.0
        if cur is not None and prev is not None:
            den=abs(prev[2]) if abs(prev[2])>1e-12 else 1.0
            f["raw_"+key+"_delta"]=(cur-prev[2])/den
    f["raw_stream_count"]=float(len(fresh))
    f["raw_freshest_lag"]=(min(fresh)/60.0) if fresh else 1.0
    return f

def make_examples(paths,raw):
    ex=[]
    for ticker,pts in paths.items():
        step=max(1,len(pts)//18)
        for i in range(5,len(pts)-1,step):
            ts,seq,p0,sp=pts[i]
            fut=[x for x in pts[i+1:] if 0<(x[0]-ts).total_seconds()<=300]
            if len(fut)<3: continue
            y=None; first_hit=None
            for ft,fs,fp,fsp in fut:
                if fp-p0>=0.05: y=1; first_hit=(ft-ts).total_seconds(); break
                if fp-p0<=-0.05: y=0; first_hit=(ft-ts).total_seconds(); break
            if y is None: continue
            past=pts[max(0,i-10):i+1]
            dt=max((ts-past[0][0]).total_seconds(),1e-9)
            prices=[x[2] for x in past]
            kf={
                "kalshi_velocity":(p0-prices[0])/dt,
                "kalshi_last_delta":p0-prices[-2],
                "kalshi_range":max(prices)-min(prices),
                "kalshi_reversal":(prices[-1]-prices[-2])*(prices[-2]-prices[-3])<0,
                "kalshi_spread":sp if sp is not None else 0.0,
                "kalshi_spread_present":1.0 if sp is not None else 0.0,
                "kalshi_price":p0,
            }
            rf=raw_features(raw,ts)
            if rf.get("raw_stream_count",0)<=0: continue
            feat={**kf,**rf}
            ex.append({"ts":ts,"ticker":ticker,"seq":seq,"y":y,"hit_s":first_hit,"f":feat})
    ex.sort(key=lambda x:x["ts"])
    return ex

def split(ex):
    cut=int(len(ex)*0.70)
    return ex[:cut],ex[cut:]

def feature_names(train,min_present=20):
    counts=defaultdict(int)
    for e in train:
        for k,v in e["f"].items():
            if isinstance(v,(int,float)) and math.isfinite(float(v)): counts[k]+=1
    return sorted(k for k,n in counts.items() if n>=min_present)

def fit_logistic(train,names,steps=350,lr=.06,l2=.01):
    if not train or not names: return None
    mu={k:statistics.fmean(float(e["f"].get(k,0.0)) for e in train) for k in names}
    sd={}
    for k in names:
        vals=[float(e["f"].get(k,0.0)) for e in train]
        s=statistics.pstdev(vals); sd[k]=s if s>1e-9 else 1.0
    w=[0.0]*(len(names)+1)
    for _ in range(steps):
        g=[0.0]*len(w)
        for e in train:
            x=[1.0]+[(float(e["f"].get(k,0.0))-mu[k])/sd[k] for k in names]
            z=max(-30,min(30,sum(a*b for a,b in zip(w,x))))
            p=1/(1+math.exp(-z)); err=p-e["y"]
            for j in range(len(w)): g[j]+=err*x[j]
        n=max(1,len(train))
        for j in range(len(w)):
            reg=0 if j==0 else l2*w[j]
            w[j]-=lr*(g[j]/n+reg)
    return names,mu,sd,w

def pred(model,e):
    names,mu,sd,w=model
    x=[1.0]+[(float(e["f"].get(k,0.0))-mu[k])/sd[k] for k in names]
    z=max(-30,min(30,sum(a*b for a,b in zip(w,x))))
    return 1/(1+math.exp(-z))

def metrics(model,test):
    ps=[pred(model,e) for e in test]; ys=[e["y"] for e in test]
    if not ys: return {}
    eps=1e-12
    return {
      "n":len(ys),
      "positive_rate":sum(ys)/len(ys),
      "brier":sum((p-y)**2 for p,y in zip(ps,ys))/len(ys),
      "logloss":-sum(y*math.log(max(eps,p))+(1-y)*math.log(max(eps,1-p)) for p,y in zip(ps,ys))/len(ys),
      "hit":sum((p>=.5)==bool(y) for p,y in zip(ps,ys))/len(ys),
      "ps":ps,"ys":ys
    }

rows=load_rows(); paths,raw=build_data(rows); ex=make_examples(paths,raw); train,test=split(ex)
names=feature_names(train); model=fit_logistic(train,names); m=metrics(model,test) if model else {}
status="HOLD"
if m and len(test)>=100:
    pos=sum(e["y"] for e in test)/len(test); majority=max(pos,1-pos)
    prior=sum(e["y"] for e in train)/len(train)
    prior_brier=sum((prior-e["y"])**2 for e in test)/len(test)
    # audit threshold deliberately requires both discrimination and probability improvement
    if m["hit"]>majority and m["brier"]<prior_brier: status="PROMISING_SHADOW_ONLY"
    bins=[]
    for lo in (0,.2,.4,.6,.8):
        pairs=[(p,y) for p,y in zip(m["ps"],m["ys"]) if lo<=p<(lo+.2 if lo<.8 else 1.000001)]
        if pairs: bins.append((lo,lo+.2,len(pairs),sum(p for p,y in pairs)/len(pairs),sum(y for p,y in pairs)/len(pairs)))
    confident=[(p,y) for p,y in zip(m["ps"],m["ys"]) if p>=.65 or p<=.35]
    conf_hit=(sum((p>=.5)==bool(y) for p,y in confident)/len(confident)) if confident else None
    print("[CALIBRATION_BINS]",[(a,b,n,round(mp,4),round(yr,4)) for a,b,n,mp,yr in bins])
    print("[ABSTENTION_35_65] coverage=",round(len(confident)/len(test),6),"hit=",None if conf_hit is None else round(conf_hit,6))
    print("[RICH_VS_PRIOR_BRIER_DELTA]",round(prior_brier-m["brier"],6))
    print("[RICH_VS_MAJORITY_HIT_DELTA]",round(m["hit"]-majority,6))
print("[GATE]",status)
print("[RULE] PROMISING_SHADOW_ONLY is not predictive-edge certification; production probability/direction/publication remain disabled")
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] OPA-030 calibration/abstention shadow gate audit complete")
