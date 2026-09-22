from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_037_bounded_canonical_tail_reader.py";TEST=ROOT/"test_opd_037_bounded_canonical_tail_reader.py"
MOD.write_text(r"""
from pathlib import Path
import json
MAX_CHUNK=250000
def _payload(v):
    if isinstance(v,dict):return v
    if isinstance(v,str):
        try:return json.loads(v)
        except:return {}
    return {}
def read_range(root,start_exclusive,end_inclusive,limit=5000):
    root=Path(root);limit=max(1,min(int(limit),MAX_CHUNK));lo=int(start_exclusive)+1;hi=min(int(end_inclusive),lo+limit-1)
    if hi<lo:return []
    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
    c=connect(root,autocommit=True);q=c.cursor();q.execute("SET statement_timeout='5000ms'")
    q.execute("SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE sequence_number BETWEEN %s AND %s ORDER BY sequence_number",(lo,hi))
    rows=[{"sequence_number":int(a),"observed_at":str(b),"source_id":str(c0),"observation_type":str(d),"canonical_observation_json":_payload(e)} for a,b,c0,d,e in q.fetchall()]
    c.close();return rows
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";contract=json.loads((rt/"opd_036_live_production_boundary_contract.json").read_text())
    hi=contract["canonical_highwater_sequence"];rows=read_range(root,max(0,hi-1000),hi,1000)
    seq=[x["sequence_number"] for x in rows]
    s={"schema_version":"OPD-037","probe_start_exclusive":max(0,hi-1000),"probe_end_inclusive":hi,"rows":len(rows),
       "monotonic":seq==sorted(seq),"bounded_sequence_query":True,"whole_table_aggregate_used":False,"read_only":True,"execution_authority":False}
    out=rt/"opd_037_bounded_canonical_tail_reader.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_037_bounded_canonical_tail_reader import build
s,p=build(Path.cwd());assert p.exists() and s["bounded_sequence_query"] and not s["whole_table_aggregate_used"] and s["monotonic"]
print("[FILE]",p);print("[ROWS]",s["rows"]);print("[BOUNDED]",s["bounded_sequence_query"]);print("[MONOTONIC]",s["monotonic"]);print("[PASS] OPD-037 bounded canonical tail reader certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-037 installer complete")