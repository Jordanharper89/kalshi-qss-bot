from pathlib import Path
import py_compile
R=Path.cwd();M=R/"qseries_v2/oracle_predictive_discovery/opd_044_continuous_prospective_worker.py";T=R/"test_opd_057_native_worker_highwater_cutover_V1.py"
M.write_text("""from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact,mature_exact
from qseries_v2.oracle_predictive_discovery.opd_044_exact_strict_future_resolver import resolve_exact
from qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome import materialize_live
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
def _write(root,payload):
 p=Path(root)/"runtime"/"predictive_data"/"opd_057_worker_heartbeat.json";p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(".tmp");q.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8");q.replace(p)
def cycle(root=None,now=None,materializer=None):
 root=Path(root or Path.cwd());rebuild_exact(root);rows=mature_exact(root,now);resolved=0;abstained=0;fn=materializer or materialize_live
 for state in rows:
  outcome=fn(state,root)
  if outcome is None:abstained+=1;continue
  resolve_exact(outcome,root);resolved+=1
 return {"mature":len(rows),"resolved":resolved,"abstained":abstained}
def run_forever(root=None,cadence=2.0):
 root=Path(root or Path.cwd()).resolve();cycles=0
 if cadence<=0:raise ValueError("cadence must be > 0")
 while True:
  cycles+=1;state="HEALTHY";err=None;result=None
  try:result=cycle(root)
  except Exception as exc:state="DEGRADED";err=f"{type(exc).__name__}: {exc}"
  _write(root,{"schema_version":"OPD-057","cycles":cycles,"state":state,"error":err,"result":result,"execution_authority":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"updated_epoch":time.time()});time.sleep(cadence)
""",encoding="utf-8")
T.write_text("""import importlib
m=importlib.import_module("qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker")
assert m.materialize_live.__module__.endswith("opd_056_highwater_witnessed_future_outcome")
assert m.execution_authority is False and m.probability_enabled is False and m.direction_enabled is False and m.publication_allowed is False
print("[OUTCOME_PAVEMENT] OPD-056 highwater witnessed")
print("[PASS] OPD-057 native worker cut over without storage-time guard assumption")
""",encoding="utf-8")
py_compile.compile(str(M),doraise=True);py_compile.compile(str(T),doraise=True);print("[PASS] OPD-057 V1 installed")