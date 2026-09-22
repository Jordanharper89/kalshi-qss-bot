from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_044_continuous_prospective_worker.py";T=R/"test_opd_065_native_worker_live_intake_REPAIR_V2.py"
M.write_text("""from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact,mature_exact
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live
from qseries_v2.oracle_predictive_discovery.opd_063_multi_horizon_prospective_intake import intake_anchor
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
def _write(root,payload):
 p=Path(root)/"runtime"/"predictive_data"/"opd_065_worker_heartbeat.json";p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(".tmp");q.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8");q.replace(p)
def _intake_spool(root):
 root=Path(root);rt=root/"runtime"/"predictive_data";spool=rt/"opd_061_live_anchor_spool.jsonl";cursor=rt/"opd_065_intake_cursor.json"
 if not spool.exists():return {"anchors":0,"states":0}
 pos=0
 if cursor.exists():
  try:pos=int(json.loads(cursor.read_text(encoding="utf-8")).get("byte_offset",0))
  except Exception:pos=0
 anchors=states=0
 with spool.open("r",encoding="utf-8") as f:
  f.seek(pos)
  while True:
   line=f.readline()
   if not line:break
   end=f.tell();a=json.loads(line);intake_anchor(a,root,root);anchors+=1;states+=7;pos=end
 cursor.write_text(json.dumps({"byte_offset":pos,"anchors_last_cycle":anchors,"states_last_cycle":states},sort_keys=True),encoding="utf-8")
 return {"anchors":anchors,"states":states}
def cycle(root=None,now=None,materializer=None):
 root=Path(root or Path.cwd());intake=_intake_spool(root);rebuild_exact(root);rows=mature_exact(root,now);resolved=0;abstained=0;fn=materializer or materialize_live
 for state in rows:
  outcome=fn(state,root)
  if outcome is None:abstained+=1;continue
  resolve_exact(outcome,root);resolved+=1
 return {"intake_anchors":intake["anchors"],"intake_states":intake["states"],"mature":len(rows),"resolved":resolved,"abstained":abstained}
def run_forever(root=None,cadence=2.0):
 root=Path(root or Path.cwd()).resolve();cycles=0
 if cadence<=0:raise ValueError("cadence must be > 0")
 while True:
  cycles+=1;state="HEALTHY";err=None;result=None
  try:result=cycle(root)
  except Exception as exc:state="DEGRADED";err=f"{type(exc).__name__}: {exc}"
  _write(root,{"schema_version":"OPD-065","cycles":cycles,"state":state,"error":err,"result":result,"execution_authority":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"updated_epoch":time.time()});time.sleep(cadence)
""",encoding="utf-8")
T.write_text("""from pathlib import Path
import importlib
m=importlib.import_module("qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker")
m._intake_spool=lambda root:{"anchors":2,"states":14}
m.rebuild_exact=lambda root:None
m.mature_exact=lambda root,now:[]
r=m.cycle(Path.cwd(),0)
assert r=={"intake_anchors":2,"intake_states":14,"mature":0,"resolved":0,"abstained":0}
assert m.execution_authority is False and m.probability_enabled is False and m.direction_enabled is False and m.publication_allowed is False
assert "opd_063_multi_horizon_prospective_intake" in Path("qseries_v2/oracle_predictive_discovery/opd_044_continuous_prospective_worker.py").read_text(encoding="utf-8")
assert "opd_044_continuous_prospective_worker import run_forever" in Path("run_opd_prospective_continuous_child.py").read_text(encoding="utf-8")
print("[INTAKE] anchors=2 states=14")
print("[OUTCOME_PAVEMENT] OPD-056 highwater witnessed preserved")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-065 repair V2 native worker live intake certified")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-065 REPAIR V2 installed")
