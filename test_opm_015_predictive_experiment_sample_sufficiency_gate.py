
from pathlib import Path
from qseries_v2.oracle_pre_momentum.opm_015_predictive_experiment_sample_sufficiency_gate import evaluate

s = evaluate(Path.cwd())
assert s["embargoed_examples"] > 0
assert s["distinct_contracts"] > 0
assert s["predictive_edge_proven"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
print("[SUFFICIENCY]", s)

if s["predictive_experiment_ready"]:
    print("[READY] population is large enough to begin bounded shadow predictive experiments")
else:
    print("[HOLD] predictive experiment population is not yet sufficient")
    print("[REASONS]", s["reasons"])

print("[PASS] no predictive model was fit")
print("[PASS] no edge claim was made")
print("[PASS] OPM-015 predictive experiment sample-sufficiency gate certified")
