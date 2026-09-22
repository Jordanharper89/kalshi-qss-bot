
from pathlib import Path
import hashlib,json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
def H(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
def build(root=None):
 root=Path(root or Path.cwd())
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='120000ms'")
   q.execute("SELECT source_id,observation_type,count(*),min(sequence_number),max(sequence_number), min(observed_at),max(observed_at) FROM public.oracle_canonical_observations GROUP BY source_id,observation_type ORDER BY count(*) DESC")
   rows=q.fetchall() or []
  c.rollback()
 groups=[]
 for sid,typ,n,lo,hi,first,last in rows:
  span=(last-first).total_seconds() if first and last else 0
  groups.append({"source_id":str(sid),"observation_type":str(typ),"rows":int(n),
   "min_sequence":int(lo),"max_sequence":int(hi),"first_observed_at":first,"last_observed_at":last,
   "observed_span_hours":span/3600,"observed_span_days":span/86400})
 s={"schema_version":"OPD-007","scope":"ENTIRE_POSTGRESQL_CANONICAL_HISTORY","group_count":len(groups),
    "total_rows":sum(x["rows"] for x in groups),"groups":groups,"hash":H(groups),"read_only":True,
    "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
 p=root/"runtime"/"predictive_data"/"opd_007_full_history_source_depth_census.json"
 p.write_text(json.dumps(s,indent=2,sort_keys=True,default=str));return s,p
