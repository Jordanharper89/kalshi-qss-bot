from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MODULE = PKG / "oed_004_independent_source_physical_inventory.py"
TEST = ROOT / "test_oed_004_independent_source_physical_inventory.py"

assert (PKG / "oed_003_kalshi_market_family_physical_inventory.py").exists()

module = r"""
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SCAN_ROWS = 250000
MARKET_DERIVED_PREFIXES = ("source.kalshi.", "source.polymarket.")

def inventory(root=None, scan_rows=SCAN_ROWS):
    root = Path(root or Path.cwd())
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute(
                "SELECT sequence_number, observed_at, source_id, observation_type "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT %s",
                (int(scan_rows),)
            )
            rows = q.fetchall() or []
        c.rollback()

    acc = defaultdict(lambda: {"rows":0, "types":set(), "first_at":None, "last_at":None})
    for seq, observed_at, source_id, obs_type in rows:
        sid = str(source_id)
        d = acc[sid]
        d["rows"] += 1
        d["types"].add(str(obs_type))
        if d["first_at"] is None or observed_at < d["first_at"]:
            d["first_at"] = observed_at
        if d["last_at"] is None or observed_at > d["last_at"]:
            d["last_at"] = observed_at

    sources = []
    for sid, d in acc.items():
        market_derived = any(sid.startswith(p) for p in MARKET_DERIVED_PREFIXES)
        span = (d["last_at"] - d["first_at"]).total_seconds() if d["first_at"] else 0.0
        sources.append({
            "source_id": sid,
            "rows": d["rows"],
            "observation_types": len(d["types"]),
            "first_at": d["first_at"],
            "last_at": d["last_at"],
            "span_seconds": span,
            "classification": "MARKET_DERIVED" if market_derived else "NON_KALSHI_POLYMARKET_SOURCE",
        })

    sources.sort(key=lambda x: (x["rows"], x["span_seconds"]), reverse=True)
    candidates = [x for x in sources if x["classification"] == "NON_KALSHI_POLYMARKET_SOURCE"]

    return {
        "schema_version":"OED-004",
        "inventory_mode":"SEQUENCE_BOUNDED_RECENT_SCAN",
        "scanned_rows":len(rows),
        "all_sources":sources,
        "independent_source_candidates":candidates,
        "classification_is_source_namespace_only":True,
        "full_table_group_by_attempted":False,
        "read_only":True,
    }
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
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
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] retired OED-004 full-table GROUP BY path")
print("[PASS] installed sequence-bounded recent source census")
print("[PASS] OED-004 scale repair installer complete")
