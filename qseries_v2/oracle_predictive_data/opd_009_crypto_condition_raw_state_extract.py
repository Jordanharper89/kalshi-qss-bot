
from pathlib import Path
from collections import Counter
import hashlib,json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
LIMIT=250000
def H(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
def build(root=None):
 root=Path(root or Path.cwd())
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='60000ms'")
   q.execute("SELECT sequence_number,observed_at,source_id,canonical_observation_json FROM public.oracle_canonical_observations WHERE observation_type='crypto_condition_snapshot' ORDER BY sequence_number DESC LIMIT %s",(LIMIT,));raw=q.fetchall() or []
  c.rollback()
 rows=[]
 for seq,outer,sid,obj in reversed(raw):
  try:o=obj["payload"]
  except:continue
  t=o.get("evidence_observed_at") or o.get("snapshot_at") or obj.get("observed_at")
  rows.append({"sequence_number":int(seq),"source_id":str(sid),"state_time":t,"stored_observed_at":outer,
   "asset":o.get("asset"),"condition":o.get("condition"),"metric_name":o.get("metric_name"),
   "value":o.get("value"),"unit":o.get("unit"),"direction":o.get("direction"),"basis":o.get("basis"),
   "source_family":o.get("source_family"),"market_native_reference":o.get("market_native_reference"),
   "independent_evidence":o.get("independent_evidence"),"raw_condition_state":True})
 s={"schema_version":"OPD-009","rows":rows,"row_count":len(rows),
    "assets":dict(Counter(str(x["asset"]) for x in rows)),"metrics":dict(Counter(str(x["metric_name"]) for x in rows)),
    "sources":dict(Counter(x["source_id"] for x in rows)),"hash":H(rows),"feature_side_only":True,
    "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
 p=root/"runtime"/"predictive_data"/"opd_009_crypto_condition_raw_state.json";p.write_text(json.dumps(s,indent=2,sort_keys=True,default=str));return s,p
