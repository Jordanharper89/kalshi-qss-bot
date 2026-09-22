
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_002_postgresql_raw_field_surface_inventory import inventory

s, p = inventory(Path.cwd())
assert p.exists()
assert s["bounded_rows"] > 0
assert s["group_count"] > 0
assert s["groups"]
assert s["read_only"] is True
print("[FILE]", p)
print("[SEQUENCE_WINDOW]", s["sequence_window"])
print("[BOUNDED_ROWS]", s["bounded_rows"])
print("[GROUPS]", s["group_count"])
print("[FIELD_INVENTORY_HASH]", s["field_inventory_hash"])
print("[TOP_PHYSICAL_GROUPS]")
for g in s["groups"][:25]:
    print(" ", {
        "source_id": g["source_id"],
        "observation_type": g["observation_type"],
        "rows": g["rows_in_window"],
        "field_count": g["field_count"],
        "first": g["first_observed_at"],
        "last": g["last_observed_at"],
    })
    print("   fields:", [x["json_path"] for x in g["fields"][:20]])
print("[PASS] PostgreSQL transaction was READ ONLY")
print("[PASS] raw JSON field paths discovered from physical rows")
print("[PASS] OPD-002 PostgreSQL raw-field surface inventory certified")
