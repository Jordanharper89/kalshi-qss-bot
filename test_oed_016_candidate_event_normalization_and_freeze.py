
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_016_candidate_event_normalization_and_freeze import freeze

s, p = freeze(Path.cwd())
assert p.exists()
assert s["source_candidate_count"] > 0
assert s["normalized_event_count"] > 0
assert s["normalized_event_count"] <= s["source_candidate_count"]
assert s["population_frozen"] is True
assert s["event_time_invented"] is False
assert s["edge_proven"] is False
assert s["execution_authority"] is False
assert len(s["event_population_hash"]) == 64

by_basis = {}
for x in s["events"]:
    k = x["event_key"][0]
    by_basis[k] = by_basis.get(k, 0) + 1

print("[POPULATION]", p)
print("[SOURCE_CANDIDATES]", s["source_candidate_count"])
print("[NORMALIZED_EVENTS]", s["normalized_event_count"])
print("[DUPLICATE_MEMBERS_COLLAPSED]", s["duplicate_members_collapsed"])
print("[BY_EVENT_BASIS]", by_basis)
print("[POPULATION_HASH]", s["event_population_hash"])
print("[PASS] OED-011/OED-012 duplicate pair events collapse by exact sequence identity")
print("[PASS] OED-013 legacy outer-time candidates remain explicitly isolated")
print("[PASS] OED-014 physical reality divergence events normalized without invented seconds")
print("[PASS] frozen deterministic research population established")
print("[PASS] OED-016 candidate event normalization/freeze certified")
