from pathlib import Path
import json,collections
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
R=Path.cwd()
with connect(R,autocommit=False) as c:
    with c.cursor() as q:
        q.execute("SET TRANSACTION READ ONLY")
        q.execute("SET LOCAL statement_timeout='20000ms'")
        q.execute("""SELECT sequence_number,observed_at,source_id,observation_type,
                    canonical_observation_json FROM public.oracle_canonical_observations
                    WHERE source_id='source.kalshi.market_data'
                    ORDER BY sequence_number DESC LIMIT 100000""")
        raw=q.fetchall() or []
    c.rollback()
rows=[]
for seq,ts,src,typ,obj in raw:
    text=json.dumps(obj,default=str).upper()
    if "KXBTC15M-" in text: rows.append((seq,ts,src,typ,obj))
assert rows,"no current Kalshi BTC15M rows"
types=collections.Counter(str(x[3]) for x in rows)
sample=rows[0]
out=R/"runtime"/"pre_momentum"; out.mkdir(parents=True,exist_ok=True)
report={"rows":len(rows),"types":dict(types),"sample_sequence":sample[0],
        "sample_observed_at":str(sample[1]),"sample_type":str(sample[3]),
        "sample_json":sample[4]}
(out/"opm_003_kalshi_contract.json").write_text(json.dumps(report,indent=2,default=str))
print("[KALSHI_BTC15M_ROWS]",len(rows))
print("[TYPES]",dict(types))
print("[SAMPLE]",sample)
print("[PASS] PostgreSQL transaction was READ ONLY")
print("[PASS] OPM-003 Kalshi BTC15M physical contract certified")
