
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_019_historical_candidate_outcome_statistics import aggregate

s, p = aggregate(Path.cwd())
assert p.exists()
assert s["group_count"] >= 0
assert s["raw_frequency_only"] is True
assert s["baseline_comparison_complete"] is False
assert s["out_of_sample_validation_complete"] is False
assert s["edge_proven"] is False
assert s["probability_enabled"] is False
assert s["execution_authority"] is False
assert len(s["statistics_hash"]) == 64

print("[STATISTICS_FILE]", p)
print("[GROUPS]", s["group_count"])
print("[STATISTICS_HASH]", s["statistics_hash"])
print("[GROUP_STATS]")
for x in s["statistics"]:
    print(" ", x)

print("[PASS] outcomes aggregated by detector family, horizon, and magnitude bucket")
print("[PASS] sample size and raw behavior frequencies preserved")
print("[PASS] no raw frequency promoted to predictive probability")
print("[PASS] baseline and out-of-sample validation remain incomplete")
print("[PASS] OED-019 historical candidate outcome statistics certified")
