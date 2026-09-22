
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_026_temporal_replication_robustness_gate import build
s,p=build(Path.cwd());assert p.exists() and not s["historical_secondary_oos_claimed"] and s["edge_certified_count"]==0
print("[FILE]",p);print("[EVALUATED]",s["associations_evaluated"]);print("[TEMPORAL_PASS]",s["temporal_replication_pass"]);print("[CUTS]",s["temporal_cuts"]);print("[PASS] OPD-026 temporal replication robustness gate certified")
