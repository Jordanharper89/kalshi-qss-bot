from collections import defaultdict, Counter
import json, re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
TICKER_RE=re.compile(r'\bKXBTC15M-[A-Z0-9-]+\b',re.I)
PREF=("yes_bid_dollars","yes_ask_dollars","yes_price_dollars","price_dollars","last_price_dollars")

def walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            yield str(k),v
            yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)

def ticker(x):
    for k,v in walk(x):
        if "ticker" in k.lower() and isinstance(v,str):
            m=TICKER_RE.search(v.upper())
            if m:return m.group(0)
    m=TICKER_RE.search(json.dumps(x,default=str).upper())
    return m.group(0) if m else None

def px(x):
    vals={}
    for k,v in walk(x):
        kl=k.lower()
        if kl in PREF:
            try:
                z=float(v)
                if 0<=z<=1:vals.setdefault(kl,z)
            except Exception:pass
    if "yes_price_dollars" in vals:return vals["yes_price_dollars"]
    if "price_dollars" in vals:return vals["price_dollars"]
    if "last_price_dollars" in vals:return vals["last_price_dollars"]
    if "yes_bid_dollars" in vals and "yes_ask_dollars" in vals:
        return (vals["yes_bid_dollars"]+vals["yes_ask_dollars"])/2
    return vals.get("yes_bid_dollars") or vals.get("yes_ask_dollars")

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
    try:d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:continue
    t=ticker(d);p=px(d)
    if t and p is not None:paths[t].append((ts,int(seq),float(p)))

labels=[];first_hit=Counter()
for t,pts in paths.items():
    pts=sorted(pts,key=lambda x:(x[0],x[1]))
    for i,(ts,seq,p0) in enumerate(pts):
        future=[x for x in pts[i+1:] if 0 < (x[0]-ts).total_seconds() <= 300]
        if len(future)<3:continue
        ups=[p-p0 for _,_,p in future];dns=[p0-p for _,_,p in future]
        mfe=max(ups);mae=max(dns)
        hit=None
        for ts2,_,p in future:
            move=p-p0
            if move>=0.05:hit="+5c";break
            if move<=-0.05:hit="-5c";break
        if hit:first_hit[hit]+=1
        labels.append((t,ts,p0,mfe,mae,hit,(future[-1][0]-ts).total_seconds()))

print("[CONTRACTS]",len(paths))
print("[5M_LABELS]",len(labels))
if labels:
    print("[MEAN_MFE]",round(sum(x[3] for x in labels)/len(labels),6))
    print("[MEAN_MAE]",round(sum(x[4] for x in labels)/len(labels),6))
print("[FIRST_HIT_5C]",dict(first_hit))
for x in labels[:30]:
    print("[LABEL]",x[0],"t=",x[1],"p0=",round(x[2],4),"mfe=",round(x[3],4),"mae=",round(x[4],4),"first5=",x[5],"window_s=",round(x[6],1))
print("[TARGETS] MFE,MAE,+5c_before_-5c,time_to_move,reversal")
print("[PASS] OPA-017 pre-momentum path-label reconstruction audit complete")
