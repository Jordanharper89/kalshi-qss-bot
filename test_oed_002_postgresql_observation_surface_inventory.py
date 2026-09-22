
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_002_postgresql_observation_surface_inventory import inventory

s = inventory(Path.cwd())
assert s["inventory_mode"] == "BOUNDED_RECENT_PHYSICAL_CENSUS"
assert s["sample_rows_accounted"] > 0
assert s["newest_sequence"] is not None
assert s["oldest_sequence"] is not None
assert s["newest_sequence"] >= s["oldest_sequence"]
assert s["sample_source_count"] > 0
assert s["sample_observation_type_count"] > 0
assert s["groups"]
assert s["exact_full_table_count_attempted"] is False
assert s["read_only"] is True

print("[MODE]", s["inventory_mode"])
print("[SAMPLE_ROWS]", s["sample_rows_accounted"])
print("[SEQUENCE_RANGE]", s["oldest_sequence"], "->", s["newest_sequence"])
print("[TIME_RANGE]", s["oldest_observed_at"], "->", s["newest_observed_at"])
print("[SAMPLE_SOURCES]", s["sample_source_count"])
print("[SAMPLE_OBSERVATION_TYPES]", s["sample_observation_type_count"])
print("[TOP_GROUPS]")
for row in s["groups"][:25]:
    print(" ", row)

print("[PASS] PostgreSQL transaction was READ ONLY")
print("[PASS] production-scale full-table COUNT/DISTINCT scan retired")
print("[PASS] bounded recent physical census completed")
print("[PASS] OED-002 scale repair certified")
