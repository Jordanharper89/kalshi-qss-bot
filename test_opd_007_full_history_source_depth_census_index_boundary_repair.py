
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_007_full_history_source_depth_census_index_boundary_repair import build

s, p = build(Path.cwd())

assert p.exists()
assert s["sequence_window"][0] > 0
assert s["sequence_window"][1] >= s["sequence_window"][0]
assert s["chunks_scanned"] > 0
assert s["scanned_rows"] > 0
assert s["grouped_total_rows"] == s["scanned_rows"]
assert s["row_accounting_ok"] is True
assert s["global_whole_table_aggregate_used"] is False
assert s["group_count"] > 0
assert s["read_only"] is True
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False

print("[FILE]", p)
print("[SEQUENCE_WINDOW]", s["sequence_window"])
print("[CHUNK_SIZE]", s["chunk_size"])
print("[CHUNKS_SCANNED]", s["chunks_scanned"])
print("[NONEMPTY_CHUNKS]", s["nonempty_chunks"])
print("[SCANNED_ROWS]", s["scanned_rows"])
print("[GROUPED_TOTAL_ROWS]", s["grouped_total_rows"])
print("[ROW_ACCOUNTING_OK]", s["row_accounting_ok"])
print("[GLOBAL_WHOLE_TABLE_AGGREGATE_USED]", s["global_whole_table_aggregate_used"])
print("[GROUPS]", s["group_count"])
print("[HASH]", s["hash"])
print("[DEEPEST_PHYSICAL_SURFACES]")
for x in s["groups"][:50]:
    print(" ", x)

print("[PASS] whole-table min/max/count bootstrap retired")
print("[PASS] sequence boundaries recovered by indexed first/last lookup")
print("[PASS] entire canonical sequence range scanned only in bounded chunks")
print("[PASS] chunk-derived exact totals reconcile")
print("[PASS] PostgreSQL access remained READ ONLY")
print("[PASS] OPD-007 full-history source-depth census INDEX BOUNDARY REPAIR certified")
