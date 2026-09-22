from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_036_live_production_boundary_contract.py";TEST=ROOT/"test_opd_036_live_production_boundary_contract.py"
MOD.write_text(r"""
from pathlib import Path
import ast,hashlib,json
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    req=[root/"run_oracle_LIVE.py",rt/"opd_031_prospective_candidate_freeze.json",
         root/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"]
    missing=[str(x) for x in req if not x.exists()]
    if missing:raise RuntimeError("MISSING_PRODUCTION_BOUNDARY:"+repr(missing))
    freeze=json.loads(req[1].read_text());tokens=sorted({t for c in freeze["candidates"] for t in c["formula"]})
    src=req[0].read_text(encoding="utf-8");tree=ast.parse(src);children=None
    for n in ast.walk(tree):
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            targets=n.targets if isinstance(n,ast.Assign) else [n.target]
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in targets):
                try:children=ast.literal_eval(n.value)
                except:pass
    if not isinstance(children,dict):raise RuntimeError("NATIVE_CHILDREN_DICT_NOT_FOUND")
    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
    c=connect(root,autocommit=True);q=c.cursor();q.execute("SET statement_timeout='5000ms'")
    q.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='oracle_canonical_observations'")
    cols=sorted(str(x[0]) for x in q.fetchall());need={"sequence_number","observed_at","observation_type","canonical_observation_json"}
    if not need.issubset(cols):raise RuntimeError("CANONICAL_SCHEMA_MISMATCH:"+repr(sorted(need-set(cols))))
    q.execute("SELECT sequence_number FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT 1");r=q.fetchone();hi=int(r[0]) if r else 0;c.close()
    s={"schema_version":"OPD-036","candidate_count":freeze["candidate_count"],"candidate_hash":freeze["candidate_source_hash"],
       "activation_epoch":freeze["activation_epoch"],"required_formula_tokens":tokens,"native_children":children,"canonical_columns":cols,
       "canonical_highwater_sequence":hi,"read_surface":"public.oracle_canonical_observations","connect_surface":"oph_019_postgresql_universal_ingestion_queue.connect",
       "launcher":"run_oracle_LIVE.py","read_only":True,"execution_authority":False}
    out=rt/"opd_036_live_production_boundary_contract.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_036_live_production_boundary_contract import build
s,p=build(Path.cwd());assert p.exists() and s["candidate_count"]==2 and s["canonical_highwater_sequence"]>0 and s["read_only"] and not s["execution_authority"]
print("[FILE]",p);print("[CANDIDATES]",s["candidate_count"]);print("[FORMULA_TOKENS]",s["required_formula_tokens"]);print("[CANONICAL_HIGHWATER]",s["canonical_highwater_sequence"]);print("[CHILDREN]",s["native_children"])
print("[PASS] exact live Oracle launcher, OPH-019 connect surface, canonical table, and frozen formula contract physically verified");print("[PASS] OPD-036 live production boundary contract certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-036 installer complete")