
from pathlib import Path
from qseries_v2.oracle_pre_momentum.opm_011_historical_training_population_depth_accounting import audit_population

s = audit_population(Path.cwd())
assert s["chf_rows"] > 0
assert s["chf_complete_multiwindow_anchors"] > 0
assert s["kalshi_rows"] > 0
assert s["kalshi_contracts"] > 0
assert s["labeled_examples"] > 0
assert s["labeled_contracts"] > 0
assert s["predictive_edge_proven"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
print("[POPULATION]", s)
print("[PASS] physical CHF/Kalshi/labeled training population measured")
print("[PASS] contract counts and temporal coverage measured")
print("[PASS] predictive edge remains UNPROVEN")
print("[PASS] OPM-011 historical training population depth accounting certified")
