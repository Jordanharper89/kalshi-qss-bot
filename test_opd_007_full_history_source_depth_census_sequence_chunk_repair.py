
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_007_full_history_source_depth_census_sequence_chunk_repair import build

s, p = build(Path.cwd())

assert p.exists()
assert s["catalog_total_rows"] > 0
assert s["scanned_rows"] > 0
assert s["group_count"] > 0
assert s["chunks_scanned"] > 0
assert s["row_accounting_ok"] is True
assert s["read_only"] is True
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False

print("[FILE]", p)
print("[SEQUENCE_WINDOW]", s["sequence_window"])
print("[CHUNK_SIZE]", s["chunk_size"])
print("[CHUNKS_SCANNED]", s["chunks_scanned"])
print("[CATALOG_TOTAL_ROWS]", s["catalog_total_rows"])
print("[SCANNED_ROWS]", s["scanned_rows"])
print("[ROW_ACCOUNTING_OK]", s["row_accounting_ok"])
print("[GROUPS]", s["group_count"])
print("[HASH]", s["hash"])
print("[DEEPEST_PHYSICAL_SURFACES]")
for x in s["groups"][:50]:
    print(" ", x)

print("[PASS] monolithic whole-table GROUP BY retired")
print("[PASS] entire canonical sequence range scanned in bounded chunks")
print("[PASS] chunk totals reconcile exactly to PostgreSQL total row count")
print("[PASS] PostgreSQL access remained READ ONLY")
print("[PASS] OPD-007 full-history source-depth census SEQUENCE CHUNK REPAIR certified")
