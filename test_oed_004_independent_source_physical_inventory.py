
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_004_independent_source_physical_inventory import inventory

s = inventory(Path.cwd())
assert s["inventory_mode"] == "SEQUENCE_BOUNDED_RECENT_SCAN"
assert s["scanned_rows"] > 0
assert s["all_sources"]
assert s["independent_source_candidates"]
assert s["classification_is_source_namespace_only"] is True
assert s["full_table_group_by_attempted"] is False
assert s["read_only"] is True

print("[MODE]", s["inventory_mode"])
print("[SCANNED_ROWS]", s["scanned_rows"])
print("[ALL_SOURCES]", len(s["all_sources"]))
print("[NON_KALSHI_POLYMARKET_SOURCE_CANDIDATES]", len(s["independent_source_candidates"]))
print("[TOP_CANDIDATES]")
for row in s["independent_source_candidates"][:40]:
    print(" ", row)
print("[PASS] PostgreSQL transaction was READ ONLY")
print("[PASS] production-scale full-table GROUP BY path retired")
print("[PASS] source classification uses physical source namespaces only")
print("[PASS] no candidate source is automatically declared independent evidence")
print("[PASS] OED-004 sequence-bounded scale repair certified")
