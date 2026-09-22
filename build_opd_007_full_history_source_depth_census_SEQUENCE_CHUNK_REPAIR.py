from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_predictive_data"
MOD = PKG / "opd_007_full_history_source_depth_census_sequence_chunk_repair.py"
TEST = ROOT / "test_opd_007_full_history_source_depth_census_sequence_chunk_repair.py"

assert (PKG / "opd_006_event_time_semantics_foundational_repair.py").exists()

MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict
import hashlib, json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

CHUNK = 500000
STATEMENT_TIMEOUT_MS = 30000

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()

def build(root=None):
    root = Path(root or Path.cwd())

    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='10000ms'")
            q.execute(
                "SELECT min(sequence_number), max(sequence_number), count(*) "
                "FROM public.oracle_canonical_observations"
            )
            min_seq, max_seq, total_rows = q.fetchone()
        c.rollback()

    min_seq = int(min_seq or 0)
    max_seq = int(max_seq or 0)
    total_rows = int(total_rows or 0)

    agg = defaultdict(lambda: {
        "rows": 0,
        "min_sequence": None,
        "max_sequence": None,
        "first_observed_at": None,
        "last_observed_at": None,
    })

    chunks = 0
    scanned_rows = 0
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

        for sid, typ, n, smin, smax, first, last in rows:
            key = (str(sid), str(typ))
            z = agg[key]
            z["rows"] += int(n)
            z["min_sequence"] = int(smin) if z["min_sequence"] is None else min(z["min_sequence"], int(smin))
            z["max_sequence"] = int(smax) if z["max_sequence"] is None else max(z["max_sequence"], int(smax))
            z["first_observed_at"] = first if z["first_observed_at"] is None else min(z["first_observed_at"], first)
            z["last_observed_at"] = last if z["last_observed_at"] is None else max(z["last_observed_at"], last)
            scanned_rows += int(n)

        chunks += 1
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

    payload = {
        "schema_version": "OPD-007",
        "revision": "SEQUENCE_CHUNK_REPAIR",
        "scope": "ENTIRE_POSTGRESQL_CANONICAL_HISTORY",
        "sequence_window": [min_seq, max_seq],
        "chunk_size": CHUNK,
        "chunks_scanned": chunks,
        "catalog_total_rows": total_rows,
        "scanned_rows": scanned_rows,
        "row_accounting_ok": scanned_rows == total_rows,
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
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return payload, out
""", encoding="utf-8")

TEST.write_text(r"""
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
""", encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPD-007 sequence-chunk repair installer complete")
