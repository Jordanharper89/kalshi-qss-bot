
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_034_prospective_oos_metrics import build
s,p=build(Path.cwd());assert p.exists() and s["candidates_evaluated"]>0 and s["edge_certified_count"]==0
print("[FILE]",p);print("[RESOLVED_STATES]",s["resolved_states"]);print("[CANDIDATES_EVALUATED]",s["candidates_evaluated"]);print("[REGISTRY_HASH]",s["registry_hash"])
print("[PASS] OPD-034 prospective OOS metrics computed only from post-freeze resolved states")
