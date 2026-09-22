import json,time
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_009_single_writer_persistence_bridge import certification_row,persist_one
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

ROOT=Path.cwd()
row=certification_row()
print("[TOKEN]",row["certification_token"])
used=persist_one(ROOT,row)
print("[WRITER_USED]",used)

found=None
for attempt in range(1,11):
    with connect(ROOT,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='10000ms'")
            sql=(
                "SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "WHERE source_id=%s ORDER BY sequence_number DESC LIMIT 100"
            )
            q.execute(sql,(row["source_id"],))
            rows=q.fetchall() or []
        c.rollback()
    for candidate in rows:
        try:
            text=json.dumps(candidate[4],default=str)
        except Exception:
            text=str(candidate[4])
        if row["certification_token"] in text:
            found=candidate
            break
    if found:
        break
    print("[READBACK_WAIT]",attempt)
    time.sleep(1)

assert found is not None,"CERTIFICATION_ROW_NOT_FOUND_IN_CANONICAL_POSTGRESQL"
print("[READBACK_SEQUENCE]",found[0])
print("[READBACK_SOURCE]",found[2])
print("[READBACK_TYPE]",found[3])
print("[PROBABILITY_ENABLED]",False)
print("[DIRECTION_ENABLED]",False)
print("[PUBLICATION_ALLOWED]",False)
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] CHF-010 end-to-end single-writer PostgreSQL persistence certified")
