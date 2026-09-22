from pathlib import Path

R=Path.cwd(); P=R/"qseries_v2"/"oracle_predictive_discovery"
for p in [
 P/"opd_042_live_state_to_prospective_intake_bridge.py",
 P/"opd_043_exact_horizon_maturity_to_future_outcome_loop.py",
]:
    if not p.is_file(): raise RuntimeError("missing dependency: "+str(p))

(P/"opd_044_continuous_prospective_worker.py").write_text(r'''from pathlib import Path
import json,time
from qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge import cycle as intake_cycle
from qseries_v2.oracle_predictive_discovery.opd_043_exact_horizon_maturity_to_future_outcome_loop import rebuild_queue,resolve_mature_once

execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _write(root,payload):
    p=Path(root)/"runtime"/"predictive_data"/"opd_044_worker_heartbeat.json"
    p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8"); tmp.replace(p)

def run_forever(root=None,cadence=2.0):
    root=Path(root or Path.cwd()).resolve()
    if cadence<=0: raise ValueError("cadence must be > 0")
    rebuild_queue(root)
    cycles=0
    while True:
        cycles+=1; state="HEALTHY"; err=None
        try:
            intake=intake_cycle(root)
            maturity=resolve_mature_once(root)
        except Exception as exc:
            intake=None; maturity=None; state="DEGRADED"; err=f"{type(exc).__name__}: {exc}"
        _write(root,{"schema_version":"OPD-044","cycles":cycles,"state":state,
          "error":err,"intake_result":repr(intake)[:2000],"maturity_result":repr(maturity)[:2000],
          "execution_authority":False,"probability_enabled":False,
          "direction_enabled":False,"publication_allowed":False,"updated_epoch":time.time()})
        time.sleep(cadence)
''',encoding="utf-8")

(R/"run_opd_prospective_continuous_child.py").write_text(r'''from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker import run_forever
if __name__=="__main__":
    run_forever(Path.cwd(),2.0)
''',encoding="utf-8")

(R/"test_opd_044_continuous_prospective_worker_child.py").write_text(r'''from pathlib import Path
import ast
from qseries_v2.oracle_predictive_discovery import opd_044_continuous_prospective_worker as m
assert m.execution_authority is False and m.probability_enabled is False
assert m.direction_enabled is False and m.publication_allowed is False
p=Path("run_opd_prospective_continuous_child.py")
assert p.is_file(); ast.parse(p.read_text(encoding="utf-8"))
assert callable(m.run_forever)
print("[PASS] OPD-044 continuous prospective child composition certified")
print("[PASS] publication/direction/probability/execution remain disabled")
''',encoding="utf-8")
print("[PASS] OPD-044 V3 installer complete")
