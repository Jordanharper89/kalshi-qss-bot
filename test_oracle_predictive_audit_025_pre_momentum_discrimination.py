from collections import defaultdict
from bisect import bisect_right
import json,re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
TICKER_RE=re.compile(r"\bKXBTC15M-[A-Z0-9-]+\b",re.I)
RAW_PREFIXES=("source.crypto.condition.btc.coinbase.","source.crypto.condition.btc.bitcoin.")
PRICE_KEYS=("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")

def walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            yield str(k),v
            yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def kalshi_parse(obj):
    try: d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception: return None,None
    text=json.dumps(d,default=str).upper(); m=TICKER_RE.search(text)
    if not m: return None,None
    vals={}
    for k,v in walk(d):
        if k.lower() in PRICE_KEYS:
            try:
                z=float(v)
                if 0<=z<=1: vals.setdefault(k.lower(),z)
            except Exception: pass
    p=vals.get("yes_price_dollars") or vals.get("price_dollars") or vals.get("last_price_dollars")
    if p is None and "yes_bid_dollars" in vals and "yes_ask_dollars" in vals:
        p=(vals["yes_bid_dollars"]+vals["yes_ask_dollars"])/2
    return m.group(0),p

rows=[];cursor=None
for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="SELECT sequence_number,observed_at,source_id,canonical_observation_json FROM public.oracle_canonical_observations"
            args=[]
            if cursor is not None: sql+=" WHERE sequence_number < %s"; args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args)); b=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(b))
    if not b: break
    rows+=b; cursor=min(int(x[0]) for x in b)

paths=defaultdict(list); raw=defaultdict(list)
for seq,ts,source,obj in rows:
    if ts is None: continue
    s=str(source)
    if s=="source.kalshi.market_data":
        t,p=kalshi_parse(obj)
        if t and p is not None: paths[t].append((ts,int(seq),float(p)))
    elif s.startswith(RAW_PREFIXES):
        raw[s].append((ts,int(seq)))

for s in raw: raw[s].sort()
raw_times={s:[x[0] for x in arr] for s,arr in raw.items()}

examples=[]
for t,pts in paths.items():
    pts=sorted(pts,key=lambda x:(x[0],x[1]))
    step=max(1,len(pts)//16)
    for i in range(3,len(pts)-1,step):
        ts,seq,p0=pts[i]
        fut=[x for x in pts[i+1:] if 0<(x[0]-ts).total_seconds()<=300]
        if len(fut)<3: continue
        y=None
        for _,_,p in fut:
            if p-p0>=0.05: y=1; break
            if p-p0<=-0.05: y=0; break
        if y is None: continue
        raw_count=0; freshest=9999.0
        for s,arr in raw.items():
            idx=bisect_right(raw_times[s],ts)-1
            if idx>=0:
                lag=(ts-arr[idx][0]).total_seconds()
                if 0<=lag<=60: raw_count+=1; freshest=min(freshest,lag)
        if raw_count:
            recent=pts[max(0,i-5):i]
            dt=max((ts-recent[0][0]).total_seconds(),1e-9)
            vel=(p0-recent[0][2])/dt
            examples.append((ts,t,p0,vel,raw_count,freshest,y))

examples.sort(key=lambda x:x[0])
cut=int(len(examples)*0.70)
train=examples[:cut]; test=examples[cut:]

def predict_rule(x):
    return 1 if (x[3]>0 and x[5]<=30) else 0

if test:
    hit=sum(predict_rule(x)==x[6] for x in test)/len(test)
    pos=sum(x[6] for x in test)/len(test)
    baseline=max(pos,1-pos)
else:
    hit=baseline=pos=None

print("[LABELED_WITH_RAW_EVIDENCE]",len(examples))
print("[CHRONOLOGICAL_SPLIT] train=",len(train),"test=",len(test),"cutoff=",test[0][0] if test else None)
print("[TEST_POSITIVE_RATE]",None if pos is None else round(pos,6))
print("[PREDECLARED_RULE_HIT_RATE]",None if hit is None else round(hit,6))
print("[MAJORITY_BASELINE_HIT_RATE]",None if baseline is None else round(baseline,6))
print("[IMPORTANT] this is discrimination feasibility only, not production predictive certification")
print("[NEXT_IF_PROMISING] richer raw-evidence deltas, order flow, spread/liquidity, regime, condition interactions, calibration")
print("[NEXT_IF_NOT_PROMISING] reject simple-rule path and test richer condition combinations without publication")
print("[NO_LEAKAGE] all features observed at or before T; labels strictly after T")
print("[PASS] OPA-025 first chronological pre-momentum discrimination audit complete")
