
from pathlib import Path
from collections import Counter
import hashlib,json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
SOURCE="source.crypto.hf.coinbase.historical_window"
LIMIT=250000
def H(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
def build(root=None):
 root=Path(root or Path.cwd())
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='60000ms'")
   q.execute("SELECT sequence_number,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s ORDER BY sequence_number DESC LIMIT %s",(SOURCE,LIMIT));raw=q.fetchall() or []
  c.rollback()
 rows=[]
 for seq,obj in reversed(raw):
  try:o=obj["payload"]["observation_payload"]
  except:continue
  if not o.get("past_only") or not o.get("full_horizon_complete"):continue
  if o.get("anchor_epoch") is None or o.get("product_id") is None:continue
  rows.append({"sequence_number":int(seq),"anchor_epoch":float(o["anchor_epoch"]),"anchor_time":o.get("anchor_time"),
   "product_id":o.get("product_id"),"window_seconds":o.get("window_seconds"),"open_price":o.get("open_price"),
   "close_price":o.get("close_price"),"return":o.get("return"),"event_count":o.get("event_count"),
   "max_event_gap_seconds":o.get("max_event_gap_seconds"),"boundary_age_seconds":o.get("boundary_age_seconds"),
   "past_only":True,"full_horizon_complete":True,"independent_external_state":True})
 s={"schema_version":"OPD-008","source_id":SOURCE,"rows":rows,"row_count":len(rows),
    "products":dict(Counter(str(x["product_id"]) for x in rows)),
    "horizons":dict(Counter(str(x["window_seconds"]) for x in rows)),"hash":H(rows),
    "feature_side_only":True,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
 p=root/"runtime"/"predictive_data"/"opd_008_coinbase_hf_raw_condition_state.json";p.write_text(json.dumps(s,indent=2,sort_keys=True,default=str));return s,p
