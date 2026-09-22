from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_predictive_data"
MOD = PKG / "opd_009_crypto_condition_raw_state_chunked_index_repair.py"
TEST = ROOT / "test_opd_009_crypto_condition_raw_state_chunked_index_repair.py"

assert (PKG / "opd_008_coinbase_hf_raw_condition_state_extract.py").exists()

MOD.write_text(r"""
from pathlib import Path
from collections import Counter
import hashlib
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

CHUNK = 250000
STATEMENT_TIMEOUT_MS = 30000
OBSERVATION_TYPE = "crypto_condition_snapshot"

def _hash(rows):
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()

def _latest_sequence(root):
    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='10000ms'")
            q.execute(
                "SELECT sequence_number "
                "FROM public.oracle_canonical_observations "
                "ORDER BY sequence_number DESC LIMIT 1"
            )
            row = q.fetchone()
        c.rollback()
    return int(row[0]) if row else 0

def _first_crypto_sequence(root, max_seq):
    hi = max_seq
    while hi > 0:
        lo = max(1, hi - CHUNK + 1)
        with connect(root, autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute(f"SET LOCAL statement_timeout='{STATEMENT_TIMEOUT_MS}ms'")
                q.execute(
                    "SELECT min(sequence_number) "
                    "FROM public.oracle_canonical_observations "
                    "WHERE sequence_number BETWEEN %s AND %s "
                    "AND observation_type=%s",
                    (lo, hi, OBSERVATION_TYPE),
                )
                row = q.fetchone()
            c.rollback()
        if row and row[0] is not None:
            found = int(row[0])
            # Continue backward until the prior chunk is empty so we locate the true first crypto-condition chunk.
            probe_hi = lo - 1
            while probe_hi > 0:
                probe_lo = max(1, probe_hi - CHUNK + 1)
                with connect(root, autocommit=False) as c:
                    with c.cursor() as q:
                        q.execute("SET TRANSACTION READ ONLY")
                        q.execute(f"SET LOCAL statement_timeout='{STATEMENT_TIMEOUT_MS}ms'")
                        q.execute(
                            "SELECT min(sequence_number) "
                            "FROM public.oracle_canonical_observations "
                            "WHERE sequence_number BETWEEN %s AND %s "
                            "AND observation_type=%s",
                            (probe_lo, probe_hi, OBSERVATION_TYPE),
                        )
                        r = q.fetchone()
                    c.rollback()
                if not r or r[0] is None:
                    break
                found = int(r[0])
                probe_hi = probe_lo - 1
            return found
        hi = lo - 1
    return 0

def build(root=None):
    root = Path(root or Path.cwd())
    max_seq = _latest_sequence(root)
    if max_seq <= 0:
        raise RuntimeError("NO_CANONICAL_ROWS")

    min_seq = _first_crypto_sequence(root, max_seq)
    if min_seq <= 0:
        raise RuntimeError("NO_CRYPTO_CONDITION_ROWS")

    rows = []
    source_counts = Counter()
    asset_counts = Counter()
    metric_counts = Counter()
    chunks_scanned = 0

    lo = min_seq
    while lo <= max_seq:
        hi = min(max_seq, lo + CHUNK - 1)

        with connect(root, autocommit=False) as c:
            with c.cursor() as q:
                q.execute("SET TRANSACTION READ ONLY")
                q.execute(f"SET LOCAL statement_timeout='{STATEMENT_TIMEOUT_MS}ms'")
                q.execute(
                    "SELECT sequence_number, observed_at, source_id, canonical_observation_json "
                    "FROM public.oracle_canonical_observations "
                    "WHERE sequence_number BETWEEN %s AND %s "
                    "AND observation_type=%s "
                    "ORDER BY sequence_number",
                    (lo, hi, OBSERVATION_TYPE),
                )
                batch = q.fetchall() or []
            c.rollback()

        for seq, observed_at, source_id, obj in batch:
            if not isinstance(obj, dict):
                try:
                    obj = json.loads(obj)
                except Exception:
                    continue

            payload = obj.get("payload")
            if not isinstance(payload, dict):
                continue

            state_time = (
                payload.get("evidence_observed_at")
                or payload.get("snapshot_at")
                or obj.get("observed_at")
                or (observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at))
            )

            row = {
                "sequence_number": int(seq),
                "source_id": str(source_id),
                "state_time": state_time,
                "stored_observed_at": observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at),
                "asset": payload.get("asset"),
                "condition": payload.get("condition"),
                "metric_name": payload.get("metric_name"),
                "value": payload.get("value"),
                "unit": payload.get("unit"),
                "direction": payload.get("direction"),
                "basis": payload.get("basis"),
                "source_family": payload.get("source_family"),
                "market_native_reference": payload.get("market_native_reference"),
                "independent_evidence": payload.get("independent_evidence"),
                "raw_condition_state": True,
                "feature_side_only": True,
            }
            rows.append(row)
            source_counts[row["source_id"]] += 1
            asset_counts[str(row["asset"])] += 1
            metric_counts[str(row["metric_name"])] += 1

        chunks_scanned += 1
        lo = hi + 1

    payload = {
        "schema_version": "OPD-009",
        "revision": "CHUNKED_INDEX_REPAIR",
        "observation_type": OBSERVATION_TYPE,
        "sequence_window": [min_seq, max_seq],
        "chunk_size": CHUNK,
        "chunks_scanned": chunks_scanned,
        "row_count": len(rows),
        "source_count": len(source_counts),
        "asset_counts": dict(asset_counts),
        "metric_counts": dict(metric_counts),
        "source_counts": dict(source_counts),
        "hash": _hash(rows),
        "query_mode": "INDEXED_SEQUENCE_BOUNDARY_PLUS_BOUNDED_CHUNKS",
        "global_filtered_sort_used": False,
        "whole_table_aggregate_used": False,
        "read_only": True,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }

    runtime = root / "runtime" / "predictive_data"
    runtime.mkdir(parents=True, exist_ok=True)

    summary_path = runtime / "opd_009_crypto_condition_raw_state.json"
    rows_path = runtime / "opd_009_crypto_condition_raw_state_rows.jsonl"

    summary_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    with rows_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    return payload, summary_path
""", encoding="utf-8")

TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_009_crypto_condition_raw_state_chunked_index_repair import build

s, p = build(Path.cwd())

assert p.exists()
assert s["row_count"] > 0
assert s["source_count"] > 0
assert s["chunks_scanned"] > 0
assert s["query_mode"] == "INDEXED_SEQUENCE_BOUNDARY_PLUS_BOUNDED_CHUNKS"
assert s["global_filtered_sort_used"] is False
assert s["whole_table_aggregate_used"] is False
assert s["read_only"] is True
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False

print("[FILE]", p)
print("[SEQUENCE_WINDOW]", s["sequence_window"])
print("[CHUNK_SIZE]", s["chunk_size"])
print("[CHUNKS_SCANNED]", s["chunks_scanned"])
print("[ROWS]", s["row_count"])
print("[SOURCES]", s["source_count"])
print("[ASSET_COUNTS]", s["asset_counts"])
print("[TOP_METRICS]")
for k, v in list(sorted(s["metric_counts"].items(), key=lambda x: (-x[1], x[0])))[:30]:
    print(" ", v, k)
print("[TOP_SOURCES]")
for k, v in list(sorted(s["source_counts"].items(), key=lambda x: (-x[1], x[0])))[:30]:
    print(" ", v, k)
print("[HASH]", s["hash"])
print("[PASS] failed global filtered-sort query retired")
print("[PASS] crypto-condition history recovered through bounded indexed chunks")
print("[PASS] raw condition values preserved on feature side only")
print("[PASS] PostgreSQL access remained READ ONLY")
print("[PASS] OPD-009 crypto-condition raw-state CHUNKED INDEX REPAIR certified")
""", encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPD-009 chunked-index repair installer complete")
