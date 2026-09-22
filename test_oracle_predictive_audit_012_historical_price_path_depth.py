from collections import Counter,defaultdict
import json,re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
ROOT=Path.cwd()
with connect(ROOT,autocommit=False) as c:
    with c.cursor() as q:
        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='15000ms'")
        q.execute("SELECT sequence_number,observed_at,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id='source.kalshi.market_data' ORDER BY sequence_number DESC LIMIT 250000")
        rows=q.fetchall() or []
    c.rollback()
by=defaultdict(list);types=Counter();price_keys=Counter()
for seq,ts,typ,obj in rows:
    types[str(typ)]+=1
    try:d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:continue
    text=json.dumps(d,separators=(",",":")).upper();m=re.search(r'KX(?:BTC|ETH|SOL)[A-Z0-9-]*',text)
    if not m:continue
    ticker=m.group(0).rstrip('"}],');by[ticker].append((seq,ts,d));stack=[d]
    while stack:
        x=stack.pop()
        if isinstance(x,dict):
            for k,v in x.items():
                if any(z in k.lower() for z in ("price","bid","ask")) and isinstance(v,(int,float,str)):price_keys[k]+=1
                if isinstance(v,(dict,list)):stack.append(v)
        elif isinstance(x,list):stack.extend(x)
print("[ROWS_SCANNED]",len(rows));print("[OBSERVATION_TYPES]",dict(types.most_common(20)))
print("[CRYPTO_CONTRACTS_WITH_ROWS]",len(by));print("[PRICE_FIELD_KEYS]",dict(price_keys.most_common(30)))
for ticker,rs in sorted(by.items(),key=lambda kv:len(kv[1]),reverse=True)[:30]:
    times=[x[1] for x in rs if x[1] is not None];span=(max(times)-min(times)).total_seconds() if len(times)>1 else 0
    print("[PATH_DEPTH]",ticker,"rows=",len(rs),"span_seconds=",round(span,3),"first=",min(times) if times else None,"last=",max(times) if times else None)
print("[PASS] OPA-012 historical Kalshi price-path depth audit complete")
