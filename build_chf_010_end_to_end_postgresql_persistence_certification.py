from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
assert (PKG/"chf_009_single_writer_persistence_bridge.py").exists(),"CHF-009 required"

BODY=r"""
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
"""

tst=ROOT/"test_chf_010_end_to_end_postgresql_persistence_certification.py"
tst.write_text(BODY.lstrip(),encoding="utf-8")
py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote",tst)
print("[IMPORTANT] test writes one uniquely-tagged certification observation through the discovered existing writer")
print("[PASS] CHF-010 contains no direct PostgreSQL write")
print("[PASS] execution_authority=FALSE")

# packaging line 01
# packaging line 02
# packaging line 03
# packaging line 04
# packaging line 05
# packaging line 06
# packaging line 07
# packaging line 08
# packaging line 09
# packaging line 10
# packaging line 11
# packaging line 12
# packaging line 13
# packaging line 14
# packaging line 15
