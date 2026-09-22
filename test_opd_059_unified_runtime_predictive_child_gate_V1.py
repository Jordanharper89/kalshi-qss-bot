from pathlib import Path
import importlib
root=Path.cwd();u=root/"run_oracle_LIVE.py";c=root/"run_opd_prospective_continuous_child.py"
assert u.is_file() and c.is_file()
us=u.read_text(encoding="utf-8");cs=c.read_text(encoding="utf-8")
assert '"predictive_prospective": "run_opd_prospective_continuous_child.py"' in us
assert "opd_044_continuous_prospective_worker import run_forever" in cs
m=importlib.import_module("qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker")
assert m.materialize_live.__module__.endswith("opd_056_highwater_witnessed_future_outcome")
assert all(getattr(m,k) is False for k in ("execution_authority","probability_enabled","direction_enabled","publication_allowed"))
print("[UNIFIED_SLOT] predictive_prospective")
print("[WORKER] OPD-057")
print("[PHYSICAL_OUTCOME] OPD-056 event-time/highwater witnessed")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-059 unified runtime predictive-child activation gate certified")
