from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data"
MOD=PKG/"opd_007_full_history_source_depth_census.py";TEST=ROOT/"test_opd_007_full_history_source_depth_census.py"
assert (PKG/"opd_006_event_time_semantics_foundational_repair.py").exists()
MOD.write_text(r"""
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
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_007_full_history_source_depth_census import build
s,p=build(Path.cwd());assert p.exists() and s["total_rows"]>0 and s["group_count"]>0 and s["read_only"]
print("[FILE]",p);print("[TOTAL_ROWS]",s["total_rows"]);print("[GROUPS]",s["group_count"]);print("[HASH]",s["hash"])
print("[DEEPEST_PHYSICAL_SURFACES]")
for x in s["groups"][:40]:print(" ",x)
print("[PASS] census covers entire canonical PostgreSQL history, not latest 250k only")
print("[PASS] source/type row depth and physical time span measured")
print("[PASS] OPD-007 full-history source-depth census certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-007 installer complete")
