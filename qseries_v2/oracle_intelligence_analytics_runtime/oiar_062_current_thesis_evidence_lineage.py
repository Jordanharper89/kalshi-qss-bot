from datetime import datetime,timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_059_thesis_calibration_readiness import read_latest_thesis_calibration_readiness
BUILD_ID="OIAR-062";STAGE="current_thesis_evidence_lineage"

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

def materialize(root=None):
 root=Path(root or Path.cwd()).resolve();src=read_latest_thesis_calibration_readiness(root)
 if not src:raise RuntimeError("OIAR-062 requires OIAR-059")
 rows=[]
 for x in src.get("markets",[]):
  rows.append({"market_id":x["market_id"],"thesis_signature":x["thesis_signature"],"factors":x.get("factors",[]),
  "direction":x.get("direction","neutral"),"research_score":x.get("research_score","0"),
  "source_stage":"deterministic_market_thesis_signature","probability":None,"calibration_status":x.get("calibration_status","UNVERIFIED")})
 return _persist(root,{"schema_version":"OIAR-062","stage":STAGE,"markets":rows,"lineage_rows":len(rows),
 "lineage_is_replayable":True,"read_only_source":True,"execution_authority":False})
def read_latest_current_thesis_evidence_lineage(root=None):return _read(root)
def physical_probe(root=None):
 x=materialize(root);return {"lineage_rows":x["lineage_rows"],"execution_authority":False}
