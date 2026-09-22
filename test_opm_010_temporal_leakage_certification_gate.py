
from pathlib import Path
from qseries_v2.oracle_pre_momentum.opm_010_temporal_leakage_certification_gate import certify

s = certify(Path.cwd())
assert s["examples"] > 0
assert s["contracts"] > 0
assert s["violations"] == []
assert s["feature_side_past_only"] is True
assert s["labels_future_only"] is True
assert s["chronological_split_plumbing_ok"] is True
assert s["predictive_edge_proven"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
print("[CERTIFICATION]", s)
print("[PASS] all feature-side observations are at or before T")
print("[PASS] all labels are strictly after T")
print("[PASS] chronological train-before-test plumbing preserved")
print("[PASS] predictive edge remains UNPROVEN")
print("[PASS] OPM-006..OPM-010 temporal pavement certified")
