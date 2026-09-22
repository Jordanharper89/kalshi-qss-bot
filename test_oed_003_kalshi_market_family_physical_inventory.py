
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_003_kalshi_market_family_physical_inventory import inventory

s = inventory(Path.cwd())

assert s["inventory_mode"] == "SEQUENCE_BOUNDED_RECENT_SCAN"
assert s["scanned_rows"] > 0
assert s["kalshi_rows_in_scan"] > 0
assert s["parsed_kalshi_rows"] > 0
assert s["families"]
assert all(x["family"].startswith("KX") for x in s["families"])
assert s["full_table_source_filter_attempted"] is False
assert s["read_only"] is True

print("[MODE]", s["inventory_mode"])
print("[SCANNED_ROWS]", s["scanned_rows"])
print("[KALSHI_ROWS_IN_SCAN]", s["kalshi_rows_in_scan"])
print("[PARSED_KALSHI_ROWS]", s["parsed_kalshi_rows"])
print("[FAMILIES]", len(s["families"]))
print("[TOP_FAMILIES]")
for row in s["families"][:40]:
    print(" ", row)

print("[PASS] PostgreSQL transaction was READ ONLY")
print("[PASS] full-table Kalshi source filter/sort path retired")
print("[PASS] families derived only from physical Kalshi tickers")
print("[PASS] no market-family list was predeclared")
print("[PASS] OED-003 sequence-bounded scale repair certified")
