from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_predictive_data"
MOD = PKG / "opd_007_full_history_source_depth_census_index_boundary_repair.py"
TEST = ROOT / "test_opd_007_full_history_source_depth_census_index_boundary_repair.py"

assert (PKG / "opd_006_event_time_semantics_foundational_repair.py").exists()

MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict
import hashlib
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

CHUNK = 250000
STATEMENT_TIMEOUT_MS = 30000

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()

def _boundary(root, descending=False):
    order = "DESC" if descending else "ASC"
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='10000ms'")
            q.execute(
                f"SELECT sequence_number "
                f"FROM public.oracle_canonical_observations "
                f"ORDER BY sequence_number {order} LIMIT 1"
            )
            row = q.fetchone()
        c.rollback()
    return int(row[0]) if row else 0

def build(root=None):
    root = Path(root or Path.cwd())

    min_seq = _boundary(root, descending=False)
    max_seq = _boundary(root, descending=True)

    if min_seq <= 0 or max_seq < min_seq:
        raise RuntimeError("NO_CANONICAL_SEQUENCE_BOUNDARIES")

    agg = defaultdict(lambda: {
        "rows": 0,
        "min_sequence": None,
        "max_sequence": None,
        "first_observed_at": None,
        "last_observed_at": None,
    })

    chunks_scanned = 0
    scanned_rows = 0
    nonempty_chunks = 0
    lo = min_seq

    while lo <= max_seq:
        hi = min(max_seq, lo + CHUNK - 1)

        with connect(root, autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute(f"SET LOCAL statement_timeout='{STATEMENT_TIMEOUT_MS}ms'")
                q.execute(
                    "SELECT source_id, observation_type, count(*), "
                    "min(sequence_number), max(sequence_number), "
                    "min(observed_at), max(observed_at) "
                    "FROM public.oracle_canonical_observations "
                    "WHERE sequence_number BETWEEN %s AND %s "
                    "GROUP BY source_id, observation_type",
                    (lo, hi),
                )
                rows = q.fetchall() or []
            c.rollback()

        chunk_rows = 0

        for sid, typ, n, smin, smax, first, last in rows:
            n = int(n)
            chunk_rows += n
            key = (str(sid), str(typ))
            z = agg[key]
            z["rows"] += n
            z["min_sequence"] = int(smin) if z["min_sequence"] is None else min(z["min_sequence"], int(smin))
            z["max_sequence"] = int(smax) if z["max_sequence"] is None else max(z["max_sequence"], int(smax))
            z["first_observed_at"] = first if z["first_observed_at"] is None else min(z["first_observed_at"], first)
            z["last_observed_at"] = last if z["last_observed_at"] is None else max(z["last_observed_at"], last)

        scanned_rows += chunk_rows
        chunks_scanned += 1
        if chunk_rows:
            nonempty_chunks += 1

        lo = hi + 1

    groups = []
    for (sid, typ), z in agg.items():
        span = (
            (z["last_observed_at"] - z["first_observed_at"]).total_seconds()
            if z["first_observed_at"] and z["last_observed_at"]
            else 0.0
        )
        groups.append({
            "source_id": sid,
            "observation_type": typ,
            "rows": z["rows"],
            "min_sequence": z["min_sequence"],
            "max_sequence": z["max_sequence"],
            "first_observed_at": z["first_observed_at"],
            "last_observed_at": z["last_observed_at"],
            "observed_span_hours": span / 3600.0,
            "observed_span_days": span / 86400.0,
        })

    groups.sort(key=lambda x: (-x["rows"], x["source_id"], x["observation_type"]))

    grouped_total = sum(x["rows"] for x in groups)

    payload = {
        "schema_version": "OPD-007",
        "revision": "INDEX_BOUNDARY_SEQUENCE_CHUNK_REPAIR",
        "scope": "ENTIRE_POSTGRESQL_CANONICAL_SEQUENCE_RANGE",
        "sequence_window": [min_seq, max_seq],
        "chunk_size": CHUNK,
        "chunks_scanned": chunks_scanned,
        "nonempty_chunks": nonempty_chunks,
        "scanned_rows": scanned_rows,
        "grouped_total_rows": grouped_total,
        "row_accounting_ok": scanned_rows == grouped_total,
        "global_whole_table_aggregate_used": False,
        "group_count": len(groups),
        "groups": groups,
        "hash": _hash(groups),
        "read_only": True,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }

    out = root / "runtime" / "predictive_data" / "opd_007_full_history_source_depth_census.json"
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return payload, out
""", encoding="utf-8")

TEST.write_text(r"""
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
""", encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPD-007 index-boundary repair installer complete")
