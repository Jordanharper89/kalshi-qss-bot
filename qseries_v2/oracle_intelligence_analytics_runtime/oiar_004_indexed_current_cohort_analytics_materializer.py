from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine import OracleMarketStatisticsEngine
from qseries_v2.oracle_intelligence.analytics.oracle_market_feature_extraction_engine import OracleCanonicalMarketFeatureExtractionEngine
from qseries_v2.oracle_intelligence.analytics.oracle_market_usefulness_scoring_engine import OracleMarketUsefulnessScoringEngine
from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_candidate_generator import OracleOpportunityCandidateGenerator
from qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import OracleOpportunityAdmissionGate

from .oiar_001_production_analytics_snapshot_foundation import (
    SNAPSHOT_TABLE,
    STATE_TABLE,
    stable_hash,
)
from .oiar_003_canonical_market_history_access_index import (
    INDEX_NAME,
    MARKET_ID_EXPRESSION,
    _index_status,
)

OIAR_004_BUILD_ID = "OIAR-004"
OIAR_004_REVISION = "OIAR_004_INDEXED_CURRENT_COHORT_ANALYTICS_MATERIALIZER_V1"

COHORT_STAGE = "reasoning_market_cohort"
ANALYTICS_STAGE = "indexed_current_cohort_oia"

def _as_dict(value):
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    raise TypeError(f"Unsupported OIA record type: {type(value)!r}")

def _load_latest_cohort(root):
    with connect(root, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(
                f"""
                SELECT payload_json
                FROM public.{SNAPSHOT_TABLE}
                WHERE stage=%s
                ORDER BY generated_at DESC, persisted_at DESC
                LIMIT 1
                """,
                (COHORT_STAGE,),
            )
            row = cur.fetchone()
        conn.rollback()

    if row is None:
        raise RuntimeError("OIAR-004 requires OIAR-002 cohort snapshot")

    payload = row[0]
    if isinstance(payload, str):
        payload = json.loads(payload)

    markets = payload.get("markets") if isinstance(payload, dict) else None
    if not isinstance(markets, list) or not markets:
        raise RuntimeError("OIAR-004 cohort payload is empty")

    ids = tuple(sorted({
        str(x.get("market_ticker") or "").strip()
        for x in markets
        if isinstance(x, dict) and str(x.get("market_ticker") or "").strip()
    }))
    if not ids:
        raise RuntimeError("OIAR-004 cohort market IDs missing")
    if len(ids) > 100:
        raise RuntimeError("OIAR-004 refuses cohort larger than 100 markets")
    return payload, ids

def _indexed_history_rows(root, market_ids, per_market=250, timeout_ms=15000):
    sql = f"""
    SELECT
        wanted.market_id,
        history.observed_at,
        history.sequence_number,
        history.yes_bid_dollars,
        history.yes_ask_dollars,
        history.last_price_dollars,
        history.volume_fp,
        history.liquidity_dollars
    FROM unnest(%s::text[]) AS wanted(market_id)
    CROSS JOIN LATERAL (
        SELECT
            observed_at,
            sequence_number,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'yes_bid_dollars' AS yes_bid_dollars,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'yes_ask_dollars' AS yes_ask_dollars,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'last_price_dollars' AS last_price_dollars,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'volume_fp' AS volume_fp,
            COALESCE(
                canonical_observation_json->'raw_observation'->'payload',
                canonical_observation_json->'payload',
                '{{}}'::jsonb
            )->>'liquidity_dollars' AS liquidity_dollars
        FROM public.oracle_canonical_observations
        WHERE observation_type='market_snapshot'
          AND ({MARKET_ID_EXPRESSION}) = wanted.market_id
        ORDER BY sequence_number DESC
        LIMIT %s
    ) AS history
    ORDER BY wanted.market_id ASC, history.sequence_number ASC
    """

    with connect(root, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'")
            cur.execute(sql, (list(market_ids), int(per_market)))
            rows = cur.fetchall() or []
        conn.rollback()

    grouped = {market_id: [] for market_id in market_ids}
    for row in rows:
        market_id = str(row[0] or "")
        if market_id in grouped:
            grouped[market_id].append(row)

    return grouped

def materialize_indexed_current_cohort_analytics(root=None, per_market=250, timeout_ms=15000):
    root = Path(root or Path.cwd()).resolve()

    exists, valid, ready, live = _index_status(root)
    if not (exists and valid and ready and live):
        raise RuntimeError("OIAR-004 requires valid OIAR-003 market-history index")

    cohort_payload, market_ids = _load_latest_cohort(root)
    grouped = _indexed_history_rows(
        root,
        market_ids,
        per_market=per_market,
        timeout_ms=timeout_ms,
    )

    connection_factory = lambda: connect(root, autocommit=False)

    statistics_engine = OracleMarketStatisticsEngine(
        connection_factory=connection_factory,
        market_limit=len(market_ids),
        history_limit_per_market=int(per_market),
    )
    feature_engine = OracleCanonicalMarketFeatureExtractionEngine(
        connection_factory=connection_factory,
        market_limit=len(market_ids),
        history_limit_per_market=int(per_market),
    )
    usefulness_engine = OracleMarketUsefulnessScoringEngine(
        connection_factory=connection_factory,
        market_limit=len(market_ids),
        history_limit_per_market=int(per_market),
    )
    candidate_engine = OracleOpportunityCandidateGenerator(
        connection_factory=connection_factory,
        market_limit=len(market_ids),
        history_limit_per_market=int(per_market),
    )
    admission_engine = OracleOpportunityAdmissionGate(
        connection_factory=connection_factory,
        market_limit=len(market_ids),
        history_limit_per_market=int(per_market),
    )

    records = []
    for market_id in market_ids:
        history = grouped.get(market_id) or []
        if not history:
            continue

        statistics = statistics_engine._calculate_market(
            market_id=market_id,
            rows=history,
        )
        features = feature_engine._extract_market(statistics)
        usefulness = usefulness_engine._score_market(features)
        candidate = candidate_engine._classify_market(features, usefulness)
        admission = admission_engine._evaluate_market(candidate)

        records.append({
            "market_id": market_id,
            "history_rows": len(history),
            "statistics": _as_dict(statistics),
            "features": _as_dict(features),
            "usefulness": _as_dict(usefulness),
            "candidate": _as_dict(candidate),
            "admission": _as_dict(admission),
        })

    records.sort(key=lambda x: x["market_id"])

    payload = {
        "schema_version": "OIAR-004",
        "stage": ANALYTICS_STAGE,
        "cohort_market_count": len(market_ids),
        "analytics_market_count": len(records),
        "per_market_history_limit": int(per_market),
        "source_index": INDEX_NAME,
        "learner_state_hash": str(cohort_payload.get("learner_state_hash") or ""),
        "lineage_current": bool(cohort_payload.get("lineage_current")),
        "markets": records,
        "read_only_source": True,
        "execution_authority": False,
    }

    if payload["analytics_market_count"] <= 0:
        raise RuntimeError("OIAR-004 produced no analytics markets")

    payload_hash = stable_hash(payload)
    snapshot_id = f"oiar-004-{payload_hash[:32]}"
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
                    ANALYTICS_STAGE,
                    "OIAR-004",
                    OIAR_004_BUILD_ID,
                    generated,
                    payload["analytics_market_count"],
                    json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str),
                    payload_hash,
                ),
            )
            cur.execute(
                f"""
                UPDATE public.{STATE_TABLE}
                SET last_successful_snapshot_id=%s,
                    last_successful_stage=%s,
                    last_successful_at=%s,
                    last_completed_at=%s,
                    status='IDLE',
                    last_error_type=NULL,
                    last_error_message=NULL,
                    updated_at=clock_timestamp()
                WHERE state_id=1
                """,
                (snapshot_id, ANALYTICS_STAGE, generated, generated),
            )
        conn.commit()

    return payload

def read_latest_indexed_current_cohort_analytics(root=None):
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
                (ANALYTICS_STAGE,),
            )
            row = cur.fetchone()
        conn.rollback()

    if row is None:
        return None

    payload, payload_hash = row
    if isinstance(payload, str):
        payload = json.loads(payload)

    if stable_hash(payload) != str(payload_hash):
        raise RuntimeError("OIAR-004 persisted snapshot hash mismatch")

    return payload
