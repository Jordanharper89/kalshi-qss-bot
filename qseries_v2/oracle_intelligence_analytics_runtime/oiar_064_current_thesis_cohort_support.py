from datetime import datetime,timezone
from pathlib import Path
from collections import Counter
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_061_current_thesis_registry import read_latest_current_thesis_registry
BUILD_ID="OIAR-064";STAGE="current_thesis_cohort_support"

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
 root=Path(root or Path.cwd()).resolve();src=read_latest_current_thesis_registry(root)
 if not src:raise RuntimeError("OIAR-064 requires OIAR-061")
 rows=[]
 for x in src.get("markets",[]):
  n=int(x.get("current_market_count",0))
  rows.append({"thesis_signature":x["thesis_signature"],"current_market_count":n,
  "cohort_status":"MULTI_MARKET" if n>1 else "SINGLE_MARKET",
  "settled_outcomes":0,"empirical_rate":None,"historical_support_status":"NOT_YET_LINKED"})
 return _persist(root,{"schema_version":"OIAR-064","stage":STAGE,"markets":rows,
 "multi_market_cohorts":sum(x["cohort_status"]=="MULTI_MARKET" for x in rows),
 "historical_outcomes_required_for_probability":True,"read_only_source":True,"execution_authority":False})
def read_latest_current_thesis_cohort_support(root=None):return _read(root)
def physical_probe(root=None):
 x=materialize(root);return {"cohorts":len(x["markets"]),"multi_market_cohorts":x["multi_market_cohorts"],"execution_authority":False}
