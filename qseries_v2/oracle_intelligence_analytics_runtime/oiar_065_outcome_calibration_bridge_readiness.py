from datetime import datetime,timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_064_current_thesis_cohort_support import read_latest_current_thesis_cohort_support
BUILD_ID="OIAR-065";STAGE="outcome_calibration_bridge_readiness"

def _persist(root, body):
    h=stable_hash(body);sid=BUILD_ID.lower()+"-"+h[:32]
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}
        (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)
        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",
        (sid,STAGE,BUILD_ID,BUILD_ID,datetime.now(timezone.utc),len(body.get("markets",[])),
        json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()
    return body
def _read(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute("SET TRANSACTION READ ONLY")
        q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,))
        r=q.fetchone();c.rollback()
    if not r:return None
    p,h=r
    if isinstance(p,str):p=json.loads(p)
    if stable_hash(p)!=str(h):raise RuntimeError(BUILD_ID+" snapshot hash mismatch")
    return p

REQUIRED_OUTCOME_FIELDS=("market_id","settled_at","outcome","evidence_cutoff_sequence","source_lineage")
def materialize(root=None):
 root=Path(root or Path.cwd()).resolve();src=read_latest_current_thesis_cohort_support(root)
 if not src:raise RuntimeError("OIAR-065 requires OIAR-064")
 rows=[{"thesis_signature":x["thesis_signature"],"historical_support_status":x["historical_support_status"],
 "settled_outcomes":0,"empirical_rate":None} for x in src.get("markets",[])]
 body={"schema_version":"OIAR-065","stage":STAGE,"markets":rows,
 "required_outcome_fields":list(REQUIRED_OUTCOME_FIELDS),
 "bridge_status":"READY_FOR_CERTIFIED_OUTCOME_SOURCE_DISCOVERY",
 "outcome_source_bound":False,"probability_enabled":False,
 "read_only_source":True,"execution_authority":False}
 return _persist(root,body)
def read_latest_outcome_calibration_bridge_readiness(root=None):return _read(root)
def physical_probe(root=None):
 x=materialize(root);return {"cohorts":len(x["markets"]),"bridge_status":x["bridge_status"],
 "outcome_source_bound":x["outcome_source_bound"],"probability_enabled":x["probability_enabled"],"execution_authority":False}
