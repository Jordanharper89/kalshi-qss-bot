from datetime import datetime,timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_057_current_market_evidence_vector import read_latest_current_market_evidence_vectors
BUILD_ID="OIAR-063";STAGE="current_thesis_contradiction_profile"

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
 root=Path(root or Path.cwd()).resolve();src=read_latest_current_market_evidence_vectors(root)
 if not src:raise RuntimeError("OIAR-063 requires OIAR-057")
 rows=[]
 for x in src.get("markets",[]):
  e=x.get("evidence",{});neg=sorted(set(e.get("negative_factors",[])));pos=sorted(set(e.get("positive_factors",[])))
  rows.append({"market_id":x["market_id"],"rank":x["rank"],"positive_factors":pos,"contradictions":neg,
  "contradiction_count":len(neg),"has_contradiction":bool(neg)})
 return _persist(root,{"schema_version":"OIAR-063","stage":STAGE,"markets":rows,
 "markets_with_contradictions":sum(x["has_contradiction"] for x in rows),"read_only_source":True,"execution_authority":False})
def read_latest_current_thesis_contradiction_profile(root=None):return _read(root)
def physical_probe(root=None):
 x=materialize(root);return {"markets":len(x["markets"]),"with_contradictions":x["markets_with_contradictions"],"execution_authority":False}
