
from __future__ import annotations
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_terminal.oracle_historical_experience_read_model import load_historical_experience_read_model
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_048_current_market_relevance_cohort_selector import STAGE as SOURCE_STAGE
OIAR_049_BUILD_ID="OIAR-049";STAGE="current_trader_cohort_historical_enrichment";EXECUTION_AUTHORITY=False
def _latest(root):
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(SOURCE_STAGE,));r=cur.fetchone()
  c.rollback()
 if not r:raise RuntimeError("OIAR-049 requires OIAR-048")
 p,h=r
 if isinstance(p,str):p=json.loads(p)
 if stable_hash(p)!=str(h):raise RuntimeError("source hash mismatch")
 return p
def _family(t):return str(t or "").split("-",1)[0] or "UNKNOWN"
def enrich_current_cohort(root=None):
 root=Path(root or Path.cwd()).resolve();src=_latest(root);model=load_historical_experience_read_model(root);fam=dict(model.learned_family_counts);exact=dict(model.learned_market_counts);rows=[]
 for raw in src["markets"]:
  x=dict(raw);t=x["market_ticker"];f=_family(t);x.update({"historical_family":f,"historical_family_records":int(fam.get(f,0)),"historical_exact_records":int(exact.get(t,0)),"historical_known":bool(fam.get(f,0) or exact.get(t,0))});rows.append(x)
 p={"schema_version":"OIAR-049","stage":STAGE,"market_count":len(rows),"learner_state_hash":str(model.learner_state_hash or ""),"lineage_current":bool(model.lineage_current),"markets":rows,"read_only_source":True,"execution_authority":False};h=stable_hash(p);sid="oiar-049-"+h[:32]
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:cur.execute(f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",(sid,STAGE,"OIAR-049",OIAR_049_BUILD_ID,len(rows),json.dumps(p,sort_keys=True),h))
  c.commit()
 return sid,p
def physical_probe(root=None):
 sid,p=enrich_current_cohort(root);return {"snapshot_id":sid,"current_markets":p["market_count"],"historically_known":sum(x["historical_known"] for x in p["markets"]),"learner_state_hash":p["learner_state_hash"],"execution_authority":False}
