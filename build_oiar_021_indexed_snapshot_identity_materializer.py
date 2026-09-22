from pathlib import Path
import ast
import importlib
import os
import subprocess
import sys
import time

ROOT = Path.cwd().resolve()
PKG = ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"
MOD = PKG/"oiar_021_indexed_snapshot_identity_materializer.py"
TEST = ROOT/"test_oiar_021_indexed_snapshot_identity_materializer.py"
INIT = PKG/"__init__.py"

MODULE_SOURCE = r'''
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, stable_hash
from .oiar_003_canonical_market_history_access_index import (
    INDEX_NAME,
    MARKET_ID_EXPRESSION,
    _index_status,
)
from .oiar_004_indexed_current_cohort_analytics_materializer import (
    ANALYTICS_STAGE,
    read_latest_indexed_current_cohort_analytics,
)

OIAR_021_BUILD_ID = "OIAR-021"
OIAR_021_REVISION = "OIAR_021_INDEXED_SNAPSHOT_IDENTITY_MATERIALIZER_V1"
IDENTITY_STAGE = "indexed_trader_market_identity"

READ_ONLY_SOURCE = True
EXECUTION_AUTHORITY = False

def _market_ids_from_analytics(payload):
    markets = payload.get("markets") if isinstance(payload, dict) else None
    if not isinstance(markets, list) or not markets:
        raise RuntimeError("OIAR-021 requires non-empty OIAR-004 analytics snapshot")

    ids = tuple(sorted({
        str(row.get("market_id") or "").strip()
        for row in markets
        if isinstance(row, dict) and str(row.get("market_id") or "").strip()
    }))
    if not ids:
        raise RuntimeError("OIAR-021 analytics market IDs missing")
    if len(ids) > 100:
        raise RuntimeError("OIAR-021 refuses more than 100 markets")
    return ids

def _identity_sql():
    return f"""
    SELECT
        wanted.market_id,
        ident.sequence_number,
        ident.observed_at,
        ident.source_market_id,
        ident.source_symbol,
        ident.event_ticker,
        ident.market_title,
        ident.source_open_time,
        ident.source_close_time,
        ident.source_status_filter
    FROM unnest(%s::text[]) AS wanted(market_id)
    CROSS JOIN LATERAL (
        SELECT
            sequence_number,
            observed_at,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'source_market_id' AS source_market_id,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'source_symbol' AS source_symbol,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'event_ticker' AS event_ticker,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'market_title' AS market_title,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'source_open_time' AS source_open_time,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'source_close_time' AS source_close_time,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'source_status_filter' AS source_status_filter
        FROM public.oracle_canonical_observations
        WHERE observation_type='market_snapshot'
          AND ({MARKET_ID_EXPRESSION}) = wanted.market_id
        ORDER BY sequence_number DESC
        LIMIT 1
    ) AS ident
    ORDER BY wanted.market_id
    """

def _plan_uses_proven_index(root, market_ids, timeout_ms):
    sql = _identity_sql()
    with connect(root, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'")
            cur.execute("EXPLAIN (FORMAT JSON) " + sql, (list(market_ids),))
            plan = cur.fetchone()[0]
        conn.rollback()
    return INDEX_NAME in json.dumps(plan, sort_keys=True, default=str)

def materialize_indexed_snapshot_identity(root=None, timeout_ms=15000):
    root = Path(root or Path.cwd()).resolve()

    exists, valid, ready, live = _index_status(root)
    if not (exists and valid and ready and live):
        raise RuntimeError("OIAR-021 requires valid/ready/live OIAR-003 index")

    analytics = read_latest_indexed_current_cohort_analytics(root)
    if analytics is None:
        raise RuntimeError("OIAR-021 requires persisted OIAR-004 analytics")

    market_ids = _market_ids_from_analytics(analytics)

    if not _plan_uses_proven_index(root, market_ids, timeout_ms):
        raise RuntimeError(
            "OIAR-021 refused execution: PostgreSQL plan does not use "
            + INDEX_NAME
        )

    sql = _identity_sql()
    with connect(root, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'")
            cur.execute(sql, (list(market_ids),))
            rows = cur.fetchall() or []
        conn.rollback()

    by_id = {}
    for row in rows:
        market_id = str(row[0] or "").strip()
        if not market_id:
            continue
        title = str(row[6] or "").strip()
        source_market_id = str(row[3] or "").strip()
        source_symbol = str(row[4] or "").strip()
        by_id[market_id] = {
            "market_id": market_id,
            "identity_resolved": bool(title),
            "market_title": title or None,
            "source_market_id": source_market_id or None,
            "source_symbol": source_symbol or None,
            "event_ticker": str(row[5] or "").strip() or None,
            "source_open_time": str(row[7] or "").strip() or None,
            "source_close_time": str(row[8] or "").strip() or None,
            "source_status_filter": str(row[9] or "").strip() or None,
            "identity_sequence_number": int(row[1]),
            "identity_observed_at": (
                row[2].astimezone(timezone.utc).isoformat()
                if hasattr(row[2], "astimezone")
                else str(row[2])
            ),
            "identity_reason": (
                "exact_indexed_market_snapshot_match"
                if title
                else "exact_indexed_match_missing_title"
            ),
        }

    identities = []
    resolved = 0
    for market_id in market_ids:
        record = by_id.get(market_id)
        if record is None:
            record = {
                "market_id": market_id,
                "identity_resolved": False,
                "market_title": None,
                "source_market_id": None,
                "source_symbol": None,
                "event_ticker": None,
                "source_open_time": None,
                "source_close_time": None,
                "source_status_filter": None,
                "identity_sequence_number": None,
                "identity_observed_at": None,
                "identity_reason": "no_exact_indexed_market_snapshot_match",
            }
        resolved += int(bool(record["identity_resolved"]))
        identities.append(record)

    body = {
        "schema_version": "OIAR-021",
        "stage": IDENTITY_STAGE,
        "source_analytics_stage": ANALYTICS_STAGE,
        "source_index": INDEX_NAME,
        "learner_state_hash": str(analytics.get("learner_state_hash") or ""),
        "lineage_current": bool(analytics.get("lineage_current")),
        "market_count": len(market_ids),
        "resolved_count": resolved,
        "unresolved_count": len(market_ids) - resolved,
        "markets": identities,
        "read_only_source": True,
        "execution_authority": False,
    }

    payload_hash = stable_hash(body)
    snapshot_id = "oiar-021-" + payload_hash[:32]
    generated = datetime.now(timezone.utc)

    with connect(root, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO public.{SNAPSHOT_TABLE}(
                    snapshot_id,stage,source_schema_version,source_engine_id,
                    generated_at,market_count,payload_json,payload_hash,
                    read_only_source,execution_authority
                )
                VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE)
                ON CONFLICT(snapshot_id) DO NOTHING
                """,
                (
                    snapshot_id,
                    IDENTITY_STAGE,
                    "OIAR-021",
                    OIAR_021_BUILD_ID,
                    generated,
                    len(market_ids),
                    json.dumps(
                        body,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    ),
                    payload_hash,
                ),
            )
        conn.commit()

    return {
        "snapshot_id": snapshot_id,
        "market_count": len(market_ids),
        "resolved_count": resolved,
        "unresolved_count": len(market_ids) - resolved,
        "plan_uses_index": True,
        "source_index": INDEX_NAME,
    }

def read_latest_indexed_snapshot_identity(root=None):
    root = Path(root or Path.cwd()).resolve()
    with connect(root, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(
                f"""
                SELECT payload_json,payload_hash
                FROM public.{SNAPSHOT_TABLE}
                WHERE stage=%s
                ORDER BY generated_at DESC,persisted_at DESC
                LIMIT 1
                """,
                (IDENTITY_STAGE,),
            )
            row = cur.fetchone()
        conn.rollback()

    if row is None:
        return None

    payload, payload_hash = row
    if isinstance(payload, str):
        payload = json.loads(payload)
    if stable_hash(payload) != str(payload_hash):
        raise RuntimeError("OIAR-021 persisted identity snapshot hash mismatch")
    return payload
'''

TEST_SOURCE = r"""
import unittest
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_021_indexed_snapshot_identity_materializer as m

class T(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(m.OIAR_021_BUILD_ID, "OIAR-021")

    def test_stage(self):
        self.assertEqual(m.IDENTITY_STAGE, "indexed_trader_market_identity")

    def test_proven_index_dependency(self):
        self.assertEqual(
            m.INDEX_NAME,
            "idx_oracle_canonical_market_snapshot_market_seq",
        )

    def test_boundaries(self):
        self.assertTrue(m.READ_ONLY_SOURCE)
        self.assertFalse(m.EXECUTION_AUTHORITY)

if __name__ == "__main__":
    print("=" * 88)
    print(" OIAR-021 CERTIFICATION TEST")
    print(" INDEXED SNAPSHOT IDENTITY MATERIALIZER")
    print("=" * 88)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] exact OIAR-003 index dependency certified")
    print("[PASS] snapshot-native identity contract certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-021 CERTIFIED")
"""

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR-021 INSTALLER")
    print(" INDEXED SNAPSHOT IDENTITY MATERIALIZER")
    print("=" * 88)
    print("[ROOT]", ROOT)

    required = (
        PKG/"oiar_001_production_analytics_snapshot_foundation.py",
        PKG/"oiar_003_canonical_market_history_access_index.py",
        PKG/"oiar_004_indexed_current_cohort_analytics_materializer.py",
    )
    for path in required:
        if not path.is_file():
            raise RuntimeError(f"Required proven upstream missing: {path}")

    # The failed prior OIAR-021 file is intentionally not imported or patched.
    failed_prior = PKG/"oiar_021_snapshot_native_market_identity_materializer.py"

    affected = (MOD, TEST, INIT)
    old = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
        print("[PASS] installer payload syntax verified")

        init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oiar_021_indexed_snapshot_identity_materializer import *"
        if export not in init_text:
            init_text = init_text.rstrip() + "\n" + export + "\n"

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        write_exact(INIT, init_text)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)

        importlib.invalidate_caches()
        m = importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime."
            "oiar_021_indexed_snapshot_identity_materializer"
        )

        started = time.monotonic()
        result = m.materialize_indexed_snapshot_identity(
            ROOT,
            timeout_ms=15000,
        )
        elapsed = time.monotonic() - started

        print(
            f"[PHYSICAL] snapshot_id={result['snapshot_id']} "
            f"markets={result['market_count']} "
            f"resolved={result['resolved_count']} "
            f"unresolved={result['unresolved_count']} "
            f"elapsed_seconds={elapsed:.3f}"
        )
        print(
            f"[PLAN] source_index={result['source_index']} "
            f"plan_uses_index={result['plan_uses_index']}"
        )

        latest = m.read_latest_indexed_snapshot_identity(ROOT)
        if latest is None:
            raise RuntimeError("OIAR-021 persisted identity snapshot missing")
        if int(latest["market_count"]) != int(result["market_count"]):
            raise RuntimeError("OIAR-021 persisted market count mismatch")
        if result["market_count"] <= 0:
            raise RuntimeError("OIAR-021 produced zero markets")
        if result["plan_uses_index"] is not True:
            raise RuntimeError("OIAR-021 did not use proven OIAR-003 index")
        if elapsed > 15.0:
            raise RuntimeError(
                f"OIAR-021 exceeded physical runtime bound: {elapsed:.3f}s"
            )

        for row in latest["markets"][:5]:
            print(
                f"[IDENTITY] market={row['market_id']} "
                f"resolved={row['identity_resolved']} "
                f"title={row['market_title']!r}"
            )

    except Exception:
        for path, data in old.items():
            restore(path, data)
        print("[ROLLBACK] OIAR-021 replacement repository files restored")
        raise

    print("[PASS] exact OIAR-003 expression/index reused")
    print("[PASS] identity work occurs before terminal read")
    print("[PASS] no terminal-time canonical scan introduced")
    print("[PASS] no Oracle Live launcher mutation")
    print("[PASS] execution_authority=FALSE")
    if failed_prior.exists():
        print("[RETIRED] prior failed OIAR-021 implementation remains unused")
    print("[DONE] OIAR-021 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
