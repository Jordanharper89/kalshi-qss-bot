
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
