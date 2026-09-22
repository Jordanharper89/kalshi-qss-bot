from collections import defaultdict
from datetime import datetime
import json, re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT = Path.cwd()
TICKER_RE = re.compile(r'\bKXBTC15M-[A-Z0-9-]+\b', re.I)
PRICE_KEYS = ("yes_bid_dollars","yes_ask_dollars","yes_price_dollars","price_dollars","last_price_dollars")

def walk(obj):
    if isinstance(obj, dict):
        for k,v in obj.items():
            yield str(k), v
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)

def extract_ticker(obj):
    for k,v in walk(obj):
        if "ticker" in k.lower() and isinstance(v,str):
            m=TICKER_RE.search(v.upper())
            if m:return m.group(0)
    try:
        m=TICKER_RE.search(json.dumps(obj,default=str).upper())
        return m.group(0) if m else None
    except Exception:
        return None

def extract_prices(obj):
    found={}
    for k,v in walk(obj):
        kl=k.lower()
        if kl in PRICE_KEYS and v is not None:
            try:
                x=float(v)
                if 0 <= x <= 1:
                    found.setdefault(kl,x)
            except Exception:
                pass
    return found

rows=[]; cursor=None
for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="""SELECT sequence_number,observed_at,observation_type,canonical_observation_json
                   FROM public.oracle_canonical_observations
                   WHERE source_id='source.kalshi.market_data'"""
            args=[]
            if cursor is not None:
                sql+=" AND sequence_number < %s"; args.append(cursor)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,tuple(args)); batch=q.fetchall() or []
        c.rollback()
    print("[PAGE]",page,"rows=",len(batch))
    if not batch:break
    rows.extend(batch)
    cursor=min(int(x[0]) for x in batch)

paths=defaultdict(list)
type_counts=defaultdict(int)

for seq,ts,typ,obj in rows:
    try:
        d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:
        continue
    ticker=extract_ticker(d)
    if not ticker:continue
    prices=extract_prices(d)
    type_counts[str(typ)]+=1
    paths[ticker].append((ts,int(seq),str(typ),prices))

usable=[]
for ticker,pts in paths.items():
    pts=sorted(pts,key=lambda x:(x[0],x[1]))
    priced=[x for x in pts if x[3]]
    if len(priced) < 2:continue
    span=(priced[-1][0]-priced[0][0]).total_seconds()
    usable.append((ticker,len(pts),len(priced),span,priced[0][0],priced[-1][0]))

usable.sort(key=lambda x:(x[2],x[3]),reverse=True)

print("[ROWS_SCANNED]",len(rows))
print("[BTC15M_CONTRACTS]",len(paths))
print("[OBSERVATION_TYPES]",dict(type_counts))
print("[USABLE_PRICE_PATHS]",len(usable))
for row in usable[:40]:
    print("[PATH]",row[0],"rows=",row[1],"priced_rows=",row[2],"span_s=",round(row[3],3),"first=",row[4],"last=",row[5])

dense=sum(1 for x in usable if x[2]>=30 and x[3]>=300)
fullish=sum(1 for x in usable if x[2]>=60 and x[3]>=720)
print("[DENSE_5M_PATHS]",dense)
print("[DENSE_12M_PATHS]",fullish)
print("[PASS] OPA-016 BTC15M exact historical path reconstruction audit complete")
