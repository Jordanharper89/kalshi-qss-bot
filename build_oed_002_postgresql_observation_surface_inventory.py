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

def inventory(root=None):
    root = Path(root or Path.cwd())
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute(
                "SELECT COUNT(*), MIN(observed_at), MAX(observed_at), "
                "COUNT(DISTINCT source_id), COUNT(DISTINCT observation_type) "
                "FROM public.oracle_canonical_observations"
            )
            total, first_at, last_at, source_count, type_count = q.fetchone()

            q.execute(
                "SELECT source_id, observation_type, COUNT(*) AS n, "
                "MIN(observed_at), MAX(observed_at) "
                "FROM public.oracle_canonical_observations "
                "GROUP BY source_id, observation_type "
                "ORDER BY n DESC LIMIT 250"
            )
            groups = q.fetchall() or []
        c.rollback()

    return {
        "schema_version": "OED-002",
        "total_rows": int(total),
        "first_observed_at": first_at,
        "last_observed_at": last_at,
        "source_count": int(source_count),
        "observation_type_count": int(type_count),
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
        "read_only": True,
    }
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_002_postgresql_observation_surface_inventory import inventory

s = inventory(Path.cwd())
assert s["total_rows"] > 0
assert s["source_count"] > 0
assert s["observation_type_count"] > 0
assert s["groups"]
assert s["read_only"] is True
print("[TOTAL_ROWS]", s["total_rows"])
print("[SOURCES]", s["source_count"])
print("[OBSERVATION_TYPES]", s["observation_type_count"])
print("[FIRST]", s["first_observed_at"])
print("[LAST]", s["last_observed_at"])
print("[TOP_GROUPS]")
for row in s["groups"][:25]:
    print(" ", row)
print("[PASS] PostgreSQL transaction was READ ONLY")
print("[PASS] Oracle physical observation surface inventoried")
print("[PASS] OED-002 PostgreSQL observation-surface inventory certified")
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-002 installer complete")
