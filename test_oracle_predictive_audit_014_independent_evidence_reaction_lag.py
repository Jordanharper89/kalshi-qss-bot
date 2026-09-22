from collections import Counter
import json
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
ROOT=Path.cwd()
with connect(ROOT,autocommit=False) as c:
    with c.cursor() as q:
        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='15000ms'")
        q.execute("SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT 300000")
        rows=q.fetchall() or []
    c.rollback()
ind=Counter();kal=Counter();assets=Counter();ind_times=[];kal_times=[]
for seq,ts,source,typ,obj in rows:
    s=str(source);typ=str(typ)
    try:text=json.dumps(obj if isinstance(obj,dict) else json.loads(obj),separators=(",",":")).upper()
    except Exception:text=""
    asset=next((a for a in ("BTC","ETH","SOL") if a in text or a in s.upper()),None)
    if not asset:continue
    if s=="source.kalshi.market_data":
        kal[(asset,typ)]+=1
        if ts:kal_times.append(ts)
    elif ("crypto" in s.lower() or "coinbase" in s.lower() or any(x in s.lower() for x in ("bitcoin","ethereum","solana"))):
        ind[(asset,s,typ)]+=1
        if ts:ind_times.append(ts)
    assets[asset]+=1
print("[ROWS_SCANNED]",len(rows));print("[ASSET_ROWS]",dict(assets));print("[KALSHI_TYPES]",dict(kal.most_common(30)))
print("[INDEPENDENT_STREAMS]")
for k,n in ind.most_common(60):print(" ",k,"rows=",n)
print("[KALSHI_TIME_RANGE]",min(kal_times) if kal_times else None,max(kal_times) if kal_times else None)
print("[INDEPENDENT_TIME_RANGE]",min(ind_times) if ind_times else None,max(ind_times) if ind_times else None)
overlap=bool(kal_times and ind_times and max(min(kal_times),min(ind_times))<=min(max(kal_times),max(ind_times)))
print("[TIMESTAMP_OVERLAP]",overlap);print("[REACTION_LAG_RECONSTRUCTION_FEASIBLE]",overlap and bool(kal) and bool(ind))
print("[PASS] OPA-014 independent evidence versus Kalshi reaction-lag feasibility audit complete")
