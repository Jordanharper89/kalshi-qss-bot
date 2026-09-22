from collections import Counter
import json,re
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
ROOT=Path.cwd()
with connect(ROOT,autocommit=False) as c:
    with c.cursor() as q:
        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='15000ms'")
        q.execute("SELECT sequence_number,observed_at,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id='source.kalshi.market_data' ORDER BY sequence_number DESC LIMIT 250000")
        rows=q.fetchall() or []
    c.rollback()
tickers={}
for seq,ts,obj in rows:
    try:d=obj if isinstance(obj,dict) else json.loads(obj)
    except Exception:continue
    text=json.dumps(d,separators=(",",":")).upper()
    for t in re.findall(r'KX[A-Z0-9-]{4,100}',text):
        t=t.rstrip('"}],')
        if any(a in t for a in ("BTC","ETH","SOL")):tickers.setdefault(t,(seq,ts))
def family(t):return re.sub(r'-\d.*$','',t)[:60]
print("[ROWS_SCANNED]",len(rows));print("[CRYPTO_TICKERS]",len(tickers))
print("[FAMILIES]",dict(Counter(family(t) for t in tickers).most_common(40)))
for t,(seq,ts) in sorted(tickers.items(),key=lambda x:x[1][0],reverse=True)[:80]:print("[TICKER]",t,"sequence=",seq,"observed_at=",ts)
print("[15M_COUNT]",sum("15M" in t for t in tickers))
print("[1H_TEXT_COUNT]",sum(("1H" in t or "HOURLY" in t or "HOUR" in t) for t in tickers))
print("[PASS] OPA-011 Kalshi crypto contract/horizon inventory complete")
