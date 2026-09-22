from collections import defaultdict
import json,re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
TICKER_RE=re.compile(r"\bKXBTC15M-[A-Z0-9-]+\b",re.I)
PRICE_KEYS=("yes_price_dollars","price_dollars","last_price_dollars","yes_bid_dollars","yes_ask_dollars")

def walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            yield str(k),v
            yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def parse(obj):
    try: d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception: return None,None,{}
    text=json.dumps(d,default=str).upper(); m=TICKER_RE.search(text)
    if not m: return None,None,{}
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
    micro={}
    if "yes_bid_dollars" in vals: micro["bid"]=vals["yes_bid_dollars"]
    if "yes_ask_dollars" in vals: micro["ask"]=vals["yes_ask_dollars"]
    if "bid" in micro and "ask" in micro: micro["spread"]=micro["ask"]-micro["bid"]
    return m.group(0),p,micro

rows=[];cursor=None
for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY"); q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="SELECT sequence_number,observed_at,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id='source.kalshi.market_data'"
            args=[]
            if cursor is not None: sql+=" AND sequence_number < %s"; args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args)); b=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(b))
    if not b: break
    rows+=b; cursor=min(int(x[0]) for x in b)

paths=defaultdict(list)
for seq,ts,typ,obj in rows:
    t,p,m=parse(obj)
    if t and ts is not None and p is not None: paths[t].append((ts,int(seq),str(typ),float(p),m))

features=[]
for t,pts in paths.items():
    pts=sorted(pts,key=lambda x:(x[0],x[1]))
    for i in range(3,len(pts)):
        ts,seq,typ,p,m=pts[i]
        prev=pts[max(0,i-10):i]
        dt=(ts-prev[0][0]).total_seconds()
        if dt<=0: continue
        delta=p-prev[-1][3]; velocity=(p-prev[0][3])/dt; spread=m.get("spread")
        features.append((t,ts,p,delta,velocity,spread,len(prev)))

print("[CONTRACTS]",len(paths))
print("[MICROSTRUCTURE_FEATURE_ROWS]",len(features))
print("[SPREAD_FEATURE_ROWS]",sum(1 for x in features if x[5] is not None))
for x in features[:40]:
    print("[FEATURE]",x[0],"t=",x[1],"p=",round(x[2],4),"last_delta=",round(x[3],4),"velocity_per_s=",round(x[4],8),"spread=",None if x[5] is None else round(x[5],4),"lookback_n=",x[6])
print("[FEATURE_SET] pre-T price velocity, recent delta, bid/ask spread where physically available")
print("[PASS] OPA-022 Kalshi pre-momentum microstructure feature audit complete")
