from collections import defaultdict,Counter
import json,re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
TICKER_RE=re.compile(r"\bKXBTC15M-[A-Z0-9-]+\b",re.I)
PRICE_KEYS=("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")
HORIZONS=(30,60,120,300)

def walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            yield str(k),v
            yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def parse(obj):
    try: d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception: return None,None
    text=json.dumps(d,default=str).upper(); m=TICKER_RE.search(text)
    if not m: return None,None
    vals={}
    for k,v in walk(d):
        kl=k.lower()
        if kl in PRICE_KEYS:
            try:
                z=float(v)
                if 0<=z<=1: vals.setdefault(kl,z)
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
            sql="SELECT sequence_number,observed_at,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id='source.kalshi.market_data'"
            args=[]
            if cursor is not None: sql+=" AND sequence_number < %s"; args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args)); b=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(b))
    if not b: break
    rows+=b; cursor=min(int(x[0]) for x in b)

paths=defaultdict(list)
for seq,ts,obj in rows:
    t,p=parse(obj)
    if t and p is not None and ts is not None: paths[t].append((ts,int(seq),float(p)))

stats={h:Counter() for h in HORIZONS}; counts=Counter()
for t,pts in paths.items():
    pts=sorted(pts,key=lambda x:(x[0],x[1]))
    for i,(ts,seq,p0) in enumerate(pts[:-1]):
        for h in HORIZONS:
            fut=[x for x in pts[i+1:] if 0<(x[0]-ts).total_seconds()<=h]
            if len(fut)<2: continue
            counts[h]+=1
            mfe=max(p-p0 for _,_,p in fut); mae=max(p0-p for _,_,p in fut)
            first=None
            for _,_,p in fut:
                if p-p0>=0.05: first="+5c"; break
                if p-p0<=-0.05: first="-5c"; break
            if first: stats[h][first]+=1
            if mfe>=0.03: stats[h]["mfe_ge_3c"]+=1
            if mae>=0.03: stats[h]["mae_ge_3c"]+=1

print("[CONTRACTS]",len(paths))
for h in HORIZONS: print("[HORIZON]",h,"labels=",counts[h],"stats=",dict(stats[h]))
print("[TARGET_FAMILY] 30s,60s,120s,300s first-hit/MFE/MAE labels")
print("[PASS] OPA-023 multi-horizon path-target reconstruction audit complete")
