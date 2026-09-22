from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_043_exact_durable_maturity_queue.py";T=R/"test_opd_043_exact_durable_maturity_queue_V5.py"
M.parent.mkdir(parents=True,exist_ok=True)
M.write_text("""from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_039_durable_horizon_maturity_queue import rebuild,mature
execution_authority=False
def rebuild_exact(state_root=None):return rebuild(Path(state_root or Path.cwd()))
def mature_exact(state_root=None,now=None):
 rows=mature(Path(state_root or Path.cwd()),now)
 req={"state_id","ticker","observed_epoch","horizon_seconds","maturity_epoch","anchor_price","matched_family_ids"}
 if any(not isinstance(x,dict) or not req.issubset(x) for x in rows):raise RuntimeError("OPD039_MATURITY_SCHEMA_MISMATCH")
 return rows
""",encoding="utf-8")
T.write_text("""import tempfile,json
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact,mature_exact
r=Path(tempfile.mkdtemp());rt=r/"runtime/predictive_data";rt.mkdir(parents=True)
x={"state_id":"S043","anchor_id":"A043","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":5,"tokens":[],"anchor_price":.54,"matched_family_ids":[],"post_freeze":True}
(rt/"opd_032_prospective_state_ledger.jsonl").write_text(json.dumps(x)+"\\n")
s,_=rebuild_exact(r);assert s["pending"]==1
assert mature_exact(r,104.999)==[];rows=mature_exact(r,105.0);assert len(rows)==1 and rows[0]["maturity_epoch"]==105.0
print("[PENDING]",s["pending"]);print("[MATURITY_EPOCH]",rows[0]["maturity_epoch"]);print("[PASS] OPD-043 exact OPD-039 durable maturity boundary certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-043 V5 installed")
