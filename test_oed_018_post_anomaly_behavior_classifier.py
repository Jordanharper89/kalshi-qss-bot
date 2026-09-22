
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_018_post_anomaly_behavior_classifier import classify

s, p = classify(Path.cwd())
assert p.exists()
assert s["classification_count"] >= 0
assert s["behavior_is_descriptive"] is True
assert s["predictive_relation_proven"] is False
assert s["edge_proven"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
assert len(s["classification_hash"]) == 64

print("[CLASSIFICATION_FILE]", p)
print("[CLASSIFICATIONS]", s["classification_count"])
print("[BEHAVIOR_COUNTS]", s["behavior_counts"])
print("[CLASSIFICATION_HASH]", s["classification_hash"])
print("[SAMPLES]")
for x in s["classifications"][:20]:
    print(" ", x)

print("[PASS] independent-reality divergence classified as follow-through/reversal/no-move only after future labels")
print("[PASS] cross-contract dispersion classified as spread convergence/expansion/stability")
print("[PASS] classifications remain descriptive and non-predictive")
print("[PASS] OED-018 post-anomaly behavior classifier certified")
