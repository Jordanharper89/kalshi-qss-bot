
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_039_durable_horizon_maturity_queue import rebuild,mature
s,p=rebuild(Path.cwd());assert p.exists() and s["restart_rebuildable"] and s["duplicate_resolution_prevented"] and not s["execution_authority"]
print("[FILE]",p);print("[PENDING]",s["pending"]);print("[MATURE_NOW]",s["mature_now"]);print("[PASS] restart-rebuildable exact-horizon maturity queue certified");print("[PASS] OPD-039 durable maturity queue certified")
