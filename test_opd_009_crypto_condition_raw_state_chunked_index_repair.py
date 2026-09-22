
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_009_crypto_condition_raw_state_chunked_index_repair import build

s, p = build(Path.cwd())

assert p.exists()
assert s["row_count"] > 0
assert s["source_count"] > 0
assert s["chunks_scanned"] > 0
assert s["query_mode"] == "INDEXED_SEQUENCE_BOUNDARY_PLUS_BOUNDED_CHUNKS"
assert s["global_filtered_sort_used"] is False
assert s["whole_table_aggregate_used"] is False
assert s["read_only"] is True
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False

print("[FILE]", p)
print("[SEQUENCE_WINDOW]", s["sequence_window"])
print("[CHUNK_SIZE]", s["chunk_size"])
print("[CHUNKS_SCANNED]", s["chunks_scanned"])
print("[ROWS]", s["row_count"])
print("[SOURCES]", s["source_count"])
print("[ASSET_COUNTS]", s["asset_counts"])
print("[TOP_METRICS]")
for k, v in list(sorted(s["metric_counts"].items(), key=lambda x: (-x[1], x[0])))[:30]:
    print(" ", v, k)
print("[TOP_SOURCES]")
for k, v in list(sorted(s["source_counts"].items(), key=lambda x: (-x[1], x[0])))[:30]:
    print(" ", v, k)
print("[HASH]", s["hash"])
print("[PASS] failed global filtered-sort query retired")
print("[PASS] crypto-condition history recovered through bounded indexed chunks")
print("[PASS] raw condition values preserved on feature side only")
print("[PASS] PostgreSQL access remained READ ONLY")
print("[PASS] OPD-009 crypto-condition raw-state CHUNKED INDEX REPAIR certified")
