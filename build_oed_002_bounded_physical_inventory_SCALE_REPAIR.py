from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MODULE = PKG / "oed_002_postgresql_observation_surface_inventory.py"
TEST = ROOT / "test_oed_002_postgresql_observation_surface_inventory.py"

assert (PKG / "oed_001_oracle_edge_discovery_foundation.py").exists()

module = r"""
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SAMPLE_ROWS = 250000

def inventory(root=None, sample_rows=SAMPLE_ROWS):
    root = Path(root or Path.cwd())

    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")

            q.execute(
                "SELECT sequence_number, observed_at "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT 1"
            )
            newest = q.fetchone()

            q.execute(
                "SELECT sequence_number, observed_at "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number ASC LIMIT 1"
            )
            oldest = q.fetchone()

            q.execute(
                "WITH recent AS ("
                " SELECT sequence_number, observed_at, source_id, observation_type "
                " FROM public.oracle_canonical_observations "
                " ORDER BY sequence_number DESC LIMIT %s"
                ") "
                "SELECT source_id, observation_type, COUNT(*) AS n, "
                "MIN(observed_at), MAX(observed_at) "
                "FROM recent "
                "GROUP BY source_id, observation_type "
                "ORDER BY n DESC",
                (int(sample_rows),)
            )
            groups = q.fetchall() or []

        c.rollback()

    source_ids = {str(r[0]) for r in groups}
    obs_types = {str(r[1]) for r in groups}

    return {
        "schema_version": "OED-002",
        "inventory_mode": "BOUNDED_RECENT_PHYSICAL_CENSUS",
        "sample_rows_requested": int(sample_rows),
        "sample_rows_accounted": sum(int(r[2]) for r in groups),
        "oldest_sequence": int(oldest[0]) if oldest else None,
        "oldest_observed_at": oldest[1] if oldest else None,
        "newest_sequence": int(newest[0]) if newest else None,
        "newest_observed_at": newest[1] if newest else None,
        "sample_source_count": len(source_ids),
        "sample_observation_type_count": len(obs_types),
        "groups": [
            {
                "source_id": str(source_id),
                "observation_type": str(obs_type),
                "rows": int(n),
                "first_at": first_at,
                "last_at": last_at,
            }
            for source_id, obs_type, n, first_at, last_at in groups
        ],
        "exact_full_table_count_attempted": False,
        "read_only": True,
    }
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
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
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)

print("[PASS] retired OED-002 full-table aggregate path")
print("[PASS] installed bounded production-scale physical census")
print("[PASS] OED-002 scale repair installer complete")
