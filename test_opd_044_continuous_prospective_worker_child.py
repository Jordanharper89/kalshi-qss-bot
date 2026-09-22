from pathlib import Path
import ast
from qseries_v2.oracle_predictive_discovery import opd_044_continuous_prospective_worker as m
assert m.execution_authority is False and m.probability_enabled is False
assert m.direction_enabled is False and m.publication_allowed is False
p=Path("run_opd_prospective_continuous_child.py")
assert p.is_file(); ast.parse(p.read_text(encoding="utf-8"))
assert callable(m.run_forever)
print("[PASS] OPD-044 continuous prospective child composition certified")
print("[PASS] publication/direction/probability/execution remain disabled")
