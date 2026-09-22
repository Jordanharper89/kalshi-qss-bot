
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
