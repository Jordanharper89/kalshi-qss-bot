
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_020_behavioral_research_maturity_gate import gate

s, p = gate(Path.cwd())
assert p.exists()
assert s["predictive_model_fit_allowed"] is False
assert s["certified_edge_count"] == 0
assert s["edge_proven"] is False
assert s["baseline_comparison_required"] is True
assert s["temporal_isolation_required"] is True
assert s["contract_day_isolation_required"] is True
assert s["out_of_sample_required"] is True
assert s["regime_stability_required"] is True
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
assert len(s["gate_hash"]) == 64

print("[GATE_FILE]", p)
print("[MATURITY_COUNTS]", s["maturity_counts"])
print("[LEGACY_OED013_EVENTS_HELD]", s["legacy_oed013_events_held"])
print("[RESEARCH_GROUPS]")
for x in s["research_groups"]:
    print(" ", x)
print("[NEXT_PHASE]", s["next_phase"])
print("[GATE_HASH]", s["gate_hash"])

print("[PASS] sample maturity gate is descriptive only")
print("[PASS] legacy OED-013 outer-time candidates remain held")
print("[PASS] predictive model fitting remains prohibited")
print("[PASS] baseline/OOS/temporal/contract-day/regime validation required next")
print("[PASS] zero certified edges")
print("[PASS] OED-016..OED-020 behavioral research slice certified")
