from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE

OIAR_003_BUILD_ID = "OIAR-003"
INDEX_NAME = "idx_oracle_canonical_market_snapshot_market_seq"

MARKET_ID_EXPRESSION = """
COALESCE(
    NULLIF(COALESCE(
        canonical_observation_json->'raw_observation'->'payload',
        canonical_observation_json->'payload',
        '{}'::jsonb
    )->>'source_market_id',''),
    NULLIF(COALESCE(
        canonical_observation_json->'raw_observation'->'payload',
        canonical_observation_json->'payload',
        '{}'::jsonb
    )->>'market_id',''),
    NULLIF(COALESCE(
        canonical_observation_json->'raw_observation'->'payload',
        canonical_observation_json->'payload',
        '{}'::jsonb
    )->>'source_symbol','')
)
""".strip()

CREATE_INDEX_SQL = f"""
CREATE INDEX CONCURRENTLY {INDEX_NAME}
ON public.oracle_canonical_observations (
    ({MARKET_ID_EXPRESSION}),
    sequence_number DESC
)
WHERE observation_type='market_snapshot'
"""

@dataclass(frozen=True)
class CanonicalMarketHistoryIndexStatus:
    index_name:str
    exists:bool
    valid:bool
    ready:bool
    live:bool
    probe_market_ticker:str
    probe_rows:int
    plan_uses_index:bool
    read_only_probe:bool=True
    execution_authority:bool=False

def _index_status(root):
    root=Path(root).resolve()
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT i.indisvalid,i.indisready,i.indislive
                FROM pg_class c
                JOIN pg_namespace n ON n.oid=c.relnamespace
                JOIN pg_index i ON i.indexrelid=c.oid
                WHERE n.nspname='public' AND c.relname=%s
            """,(INDEX_NAME,))
            row=cur.fetchone()
    return (False,False,False,False) if row is None else (True,bool(row[0]),bool(row[1]),bool(row[2]))

def ensure_canonical_market_history_index(root=None):
    root=Path(root or Path.cwd()).resolve()
    exists,valid,ready,live=_index_status(root)

    if exists and not (valid and ready and live):
        with connect(root,autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"DROP INDEX CONCURRENTLY IF EXISTS public.{INDEX_NAME}")

    exists,valid,ready,live=_index_status(root)
    if not exists:
        with connect(root,autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout=0")
                cur.execute(CREATE_INDEX_SQL)

    return _index_status(root)

def _latest_reasoning_ticker(root):
    root=Path(root).resolve()
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"""
                SELECT payload_json
                FROM public.{SNAPSHOT_TABLE}
                WHERE stage='reasoning_market_cohort'
                ORDER BY generated_at DESC,persisted_at DESC
                LIMIT 1
            """)
            row=cur.fetchone()
        conn.rollback()

    if row is None:
        raise RuntimeError("OIAR-003 requires OIAR-002 snapshot")

    payload=row[0]
    if isinstance(payload,str):
        payload=json.loads(payload)

    markets=payload.get("markets") if isinstance(payload,dict) else None
    if not isinstance(markets,list) or not markets:
        raise RuntimeError("OIAR-003 reasoning cohort is empty")

    ticker=str(markets[0].get("market_ticker") or "").strip()
    if not ticker:
        raise RuntimeError("OIAR-003 reasoning cohort ticker missing")
    return ticker

def probe_indexed_market_history(root=None,limit=250,timeout_ms=10000):
    root=Path(root or Path.cwd()).resolve()
    exists,valid,ready,live=_index_status(root)
    if not (exists and valid and ready and live):
        raise RuntimeError("OIAR-003 index is not valid/ready/live")

    ticker=_latest_reasoning_ticker(root)

    sql=f"""
        SELECT sequence_number,observed_at
        FROM public.oracle_canonical_observations
        WHERE observation_type='market_snapshot'
          AND ({MARKET_ID_EXPRESSION})=%s
        ORDER BY sequence_number DESC
        LIMIT %s
    """

    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'")
            cur.execute("EXPLAIN (FORMAT JSON) "+sql,(ticker,int(limit)))
            plan=cur.fetchone()[0]
            cur.execute(sql,(ticker,int(limit)))
            rows=cur.fetchall() or []
        conn.rollback()

    plan_text=json.dumps(plan,sort_keys=True,default=str)
    return CanonicalMarketHistoryIndexStatus(
        INDEX_NAME,exists,valid,ready,live,ticker,len(rows),
        INDEX_NAME in plan_text,True,False
    )

def verify_oiar_003_canonical_market_history_access_index(root=None):
    x=probe_indexed_market_history(root)
    return bool(
        x.exists and x.valid and x.ready and x.live and
        x.probe_rows>0 and x.plan_uses_index and
        x.read_only_probe and not x.execution_authority
    )
