from collections import Counter
import json,re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
rows=[]
cursor=None

for page in range(1,5):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='15000ms'")
            sql="""SELECT sequence_number,observed_at,canonical_observation_json
                   FROM public.oracle_canonical_observations
                   WHERE source_id='source.kalshi.market_data'"""
            args=()
            if cursor is not None:
                sql+=" AND sequence_number < %s"
                args=(cursor,)
            sql+=" ORDER BY sequence_number DESC LIMIT 50000"
            q.execute(sql,args)
            batch=q.fetchall() or []
        c.rollback()

    print("[PAGE]",page,"rows=",len(batch))
    if not batch: break
    rows.extend(batch)
    cursor=min(int(x[0]) for x in batch)

tickers={}
for seq,ts,obj in rows:
    try:d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:continue
    text=json.dumps(d,separators=(",",":")).upper()
    for t in re.findall(r'KX[A-Z0-9-]{4,100}',text):
        t=t.rstrip('"}],')
        if any(a in t for a in ("BTC","ETH","SOL")):
            tickers.setdefault(t,(seq,ts))

def family(t):
    return re.sub(r'-\d.*$','',t)[:80]

families=Counter(family(t) for t in tickers)

print("[ROWS_SCANNED]",len(rows))
print("[CRYPTO_TICKERS]",len(tickers))
print("[FAMILIES]",dict(families.most_common(60)))
print("[15M_COUNT]",sum("15M" in t for t in tickers))

hourly=[t for t in tickers if "1H" in t or "HOURLY" in t or "HOUR" in t]
print("[1H_TEXT_COUNT]",len(hourly))

for t,(seq,ts) in sorted(tickers.items(),key=lambda x:x[1][0],reverse=True)[:120]:
    print("[TICKER]",t,"sequence=",seq,"observed_at=",ts)

print("[PASS] OPA-011 200K bounded crypto inventory complete")
