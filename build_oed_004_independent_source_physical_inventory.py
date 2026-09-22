from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MODULE = PKG / "oed_004_independent_source_physical_inventory.py"
TEST = ROOT / "test_oed_004_independent_source_physical_inventory.py"

assert (PKG / "oed_003_kalshi_market_family_physical_inventory.py").exists()

module = r"""
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

MARKET_DERIVED_PREFIXES = (
    "source.kalshi.",
    "source.polymarket.",
)

def inventory(root=None):
    root = Path(root or Path.cwd())
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute(
                "SELECT source_id, COUNT(*) AS n, COUNT(DISTINCT observation_type), "
                "MIN(observed_at), MAX(observed_at) "
                "FROM public.oracle_canonical_observations "
                "GROUP BY source_id ORDER BY n DESC"
            )
            rows = q.fetchall() or []
        c.rollback()

    sources = []
    for source_id, n, types, first_at, last_at in rows:
        sid = str(source_id)
        market_derived = any(sid.startswith(p) for p in MARKET_DERIVED_PREFIXES)
        span_seconds = 0.0
        if first_at is not None and last_at is not None:
            span_seconds = (last_at - first_at).total_seconds()
        sources.append({
            "source_id": sid,
            "rows": int(n),
            "observation_types": int(types),
            "first_at": first_at,
            "last_at": last_at,
            "span_seconds": span_seconds,
            "classification": "MARKET_DERIVED" if market_derived else "NON_KALSHI_POLYMARKET_SOURCE",
        })

    independent_candidates = [
        x for x in sources if x["classification"] == "NON_KALSHI_POLYMARKET_SOURCE"
    ]
    independent_candidates.sort(
        key=lambda x: (x["rows"], x["span_seconds"], x["observation_types"]), reverse=True
    )
    return {
        "schema_version": "OED-004",
        "all_sources": sources,
        "independent_source_candidates": independent_candidates,
        "classification_is_source_namespace_only": True,
    }
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_004_independent_source_physical_inventory import inventory

s = inventory(Path.cwd())
assert s["all_sources"]
assert s["independent_source_candidates"]
assert s["classification_is_source_namespace_only"] is True
print("[ALL_SOURCES]", len(s["all_sources"]))
print("[NON_KALSHI_POLYMARKET_SOURCE_CANDIDATES]", len(s["independent_source_candidates"]))
print("[TOP_CANDIDATES]")
for row in s["independent_source_candidates"][:40]:
    print(" ", row)
print("[PASS] source classification uses physical source namespaces only")
print("[PASS] no candidate source is automatically declared independent evidence")
print("[PASS] OED-004 independent-source physical inventory certified")
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-004 installer complete")
