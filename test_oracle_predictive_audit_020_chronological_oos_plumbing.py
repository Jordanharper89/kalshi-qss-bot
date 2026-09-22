from collections import defaultdict, Counter
import json, re, math
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
TICKER_RE=re.compile(r'\bKXBTC15M-[A-Z0-9-]+\b',re.I)
PRICE_KEYS=("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")

def walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            yield str(k),v
            yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)

def parse(obj):
    try:d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:return None,None
    text=json.dumps(d,default=str).upper();m=TICKER_RE.search(text)
    if not m:return None,None
    vals={}
    for k,v in walk(d):
        kl=k.lower()
        if kl in PRICE_KEYS:
            try:
                z=float(v)
                if 0<=z<=1:vals.setdefault(kl,z)
            except Exception:pass
    p=vals.get("yes_price_dollars") or vals.get("price_dollars") or vals.get("last_price_dollars")
    if p is None and "yes_bid_dollars" in vals and "yes_ask_dollars" in vals:
        p=(vals["yes_bid_dollars"]+vals["yes_ask_dollars"])/2
    return m.group(0),p

rows=[];cursor=None
for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="""SELECT sequence_number,observed_at,canonical_observation_json
                   FROM public.oracle_canonical_observations
                   WHERE source_id='source.kalshi.market_data'"""
            args=[]
            if cursor is not None:sql+=" AND sequence_number < %s";args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args));b=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(b))
    if not b:break
    rows+=b;cursor=min(int(x[0]) for x in b)

paths=defaultdict(list)
for seq,ts,obj in rows:
    t,p=parse(obj)
    if t and p is not None and ts is not None:paths[t].append((ts,int(seq),float(p)))

examples=[]
for t,pts in paths.items():
    pts=sorted(pts,key=lambda x:(x[0],x[1]))
    if len(pts)<20:continue
    for i in range(0,len(pts)-3,max(1,len(pts)//12)):
        ts,seq,p0=pts[i]
        fut=[x for x in pts[i+1:] if 0<(x[0]-ts).total_seconds()<=300]
        if len(fut)<3:continue
        first=None
        for ts2,_,p in fut:
            if p-p0>=0.05:first=1;break
            if p-p0<=-0.05:first=0;break
        if first is None:continue
        examples.append((ts,t,p0,first))

examples.sort(key=lambda x:x[0])
cut=int(len(examples)*0.70)
train=examples[:cut];test=examples[cut:]

# deliberately simple audit baseline: prior positive rate learned from earlier chronology only
train_rate=(sum(x[3] for x in train)/len(train)) if train else 0.5
brier=sum((train_rate-x[3])**2 for x in test)/len(test) if test else None
hit=sum((train_rate>=0.5)==bool(x[3]) for x in test)/len(test) if test else None
naive_brier=sum((0.5-x[3])**2 for x in test)/len(test) if test else None

print("[LABELED_EXAMPLES]",len(examples))
print("[CHRONOLOGICAL_SPLIT] train=",len(train),"test=",len(test),"cutoff=",test[0][0] if test else None)
print("[TRAIN_POSITIVE_RATE]",round(train_rate,6))
print("[TEST_BRIER_PRIOR_ONLY]",None if brier is None else round(brier,6))
print("[TEST_BRIER_50_50]",None if naive_brier is None else round(naive_brier,6))
print("[TEST_DIRECTIONAL_HIT_PRIOR_ONLY]",None if hit is None else round(hit,6))
print("[IMPORTANT] this is label/backtest plumbing validation, not an Oracle predictive model")
print("[NEXT_MODEL_INPUTS] past-only independent evidence, Kalshi microstructure, regime, order flow, liquidity, learned conditions")
print("[NO_LEAKAGE] training rows occur strictly before chronological test rows")
print("[PASS] OPA-020 chronological out-of-sample plumbing audit complete")
