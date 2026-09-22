
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_010_first_raw_prediction_join_readiness_gate import build
s,p=build(Path.cwd());assert p.exists() and s["raw_join_pavement_ready"];assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[CHECKS]",s["checks"]);print("[PHYSICAL_COUNTS]",s["physical_counts"]);print("[SOURCE_HASHES]",s["source_hashes"]);print("[NEXT_REQUIRED]",s["next_required"]);print("[GATE_HASH]",s["gate_hash"])
print("[PASS] raw predictive ingredients physically present")
print("[PASS] formula mining remains blocked until strict as-of state join is frozen")
print("[PASS] OPD-006..OPD-010 predictive-data dissection slice certified")
