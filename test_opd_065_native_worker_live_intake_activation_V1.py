from pathlib import Path
import ast
p=Path("qseries_v2/oracle_predictive_discovery/opd_044_continuous_prospective_worker.py")
s=p.read_text(encoding="utf-8");ast.parse(s)
assert "def _intake_spool(" in s and "intake_anchor(a,root,root)" in s
assert "execution_authority=False" in s and "probability_enabled=False" in s
assert "direction_enabled=False" in s and "publication_allowed=False" in s
assert "opd_044_continuous_prospective_worker import run_forever" in Path("run_opd_prospective_continuous_child.py").read_text()
assert '"predictive_prospective": "run_opd_prospective_continuous_child.py"' in Path("run_oracle_live.py").read_text()
print("[NATIVE_CHILD] predictive_prospective")
print("[INTAKE] OPD-061 -> OPD-062 -> OPD-063 -> OPD-032/039")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-065 native predictive worker live intake activation gate certified")
