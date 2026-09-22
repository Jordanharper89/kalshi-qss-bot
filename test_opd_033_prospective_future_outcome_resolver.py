
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_033_prospective_future_outcome_resolver import summary
s,p=summary(Path.cwd());assert p.exists() and s["resolved_states"]>=0 and s["all_strictly_future"]
print("[FILE]",p);print("[RESOLVED_STATES]",s["resolved_states"]);print("[RESOLVED_TRIGGERS]",s["resolved_trigger_states"])
print("[PASS] OPD-033 strictly-future prospective outcome resolver ready")
