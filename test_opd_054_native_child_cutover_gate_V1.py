from pathlib import Path
import importlib
root=Path.cwd();launcher=root/"run_opd_prospective_continuous_child.py";unified=root/"run_oracle_LIVE.py"
assert launcher.is_file() and unified.is_file()
ls=launcher.read_text(encoding="utf-8");us=unified.read_text(encoding="utf-8")
assert "opd_044_continuous_prospective_worker import run_forever" in ls
assert '"predictive_prospective": "run_opd_prospective_continuous_child.py"' in us
m=importlib.import_module("qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker")
assert callable(m.run_forever) and callable(m.cycle)
assert m.execution_authority is False
assert m.probability_enabled is False
assert m.direction_enabled is False
assert m.publication_allowed is False
assert m.materialize_live.__module__.endswith("opd_051_exact_witnessed_future_path_outcome")
print("[SUPERVISOR_SLOT] predictive_prospective")
print("[CHILD_LAUNCHER] run_opd_prospective_continuous_child.py")
print("[OUTCOME_PAVEMENT] OPD-051 witnessed")
print("[EXECUTION_AUTHORITY] FALSE")
print("[PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE")
print("[PASS] OPD-054 native supervised-child cutover gate certified")
