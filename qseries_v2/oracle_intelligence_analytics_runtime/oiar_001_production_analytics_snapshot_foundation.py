from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

OIAR_001_BUILD_ID="OIAR-001"
OIAR_001_REVISION="OIAR_001_PRODUCTION_ANALYTICS_SNAPSHOT_FOUNDATION_V1"

STATE_TABLE="oracle_intelligence_analytics_runtime_state"
SNAPSHOT_TABLE="oracle_intelligence_analytics_snapshots"

DDL=f"""
CREATE TABLE IF NOT EXISTS public.{STATE_TABLE}(
    state_id SMALLINT PRIMARY KEY CHECK(state_id=1),
    last_successful_snapshot_id TEXT,
    last_successful_stage TEXT,
    last_successful_at TIMESTAMPTZ,
    last_started_at TIMESTAMPTZ,
    last_completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'IDLE'
        CHECK(status IN ('IDLE','RUNNING','DEGRADED','FAILED')),
    failure_count BIGINT NOT NULL DEFAULT 0 CHECK(failure_count>=0),
    last_error_type TEXT,
    last_error_message TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

INSERT INTO public.{STATE_TABLE}(state_id,status)
VALUES(1,'IDLE')
ON CONFLICT(state_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.{SNAPSHOT_TABLE}(
    snapshot_id TEXT PRIMARY KEY,
    stage TEXT NOT NULL,
    source_schema_version TEXT,
    source_engine_id TEXT,
    generated_at TIMESTAMPTZ NOT NULL,
    persisted_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    market_count INTEGER NOT NULL CHECK(market_count>=0),
    payload_json JSONB NOT NULL,
    payload_hash TEXT NOT NULL,
    read_only_source BOOLEAN NOT NULL DEFAULT TRUE,
    execution_authority BOOLEAN NOT NULL DEFAULT FALSE
        CHECK(execution_authority=FALSE)
);

CREATE INDEX IF NOT EXISTS oracle_intelligence_analytics_snapshots_stage_time_idx
ON public.{SNAPSHOT_TABLE}(stage,generated_at DESC,persisted_at DESC);
"""

@dataclass(frozen=True)
class AnalyticsSnapshotFoundationStatus:
    state_table:str
    snapshot_table:str
    state_row_present:bool
    database_writable:bool
    read_only_source_required:bool=True
    execution_authority:bool=False

def stable_hash(value)->str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def ensure_analytics_snapshot_schema(root=None)->bool:
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
    return True

def inspect_foundation(root=None)->AnalyticsSnapshotFoundationStatus:
    root=Path(root or Path.cwd()).resolve()
    ensure_analytics_snapshot_schema(root)
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT EXISTS(SELECT 1 FROM public.{STATE_TABLE} WHERE state_id=1)"
            )
            state_present=bool(cur.fetchone()[0])

            cur.execute("CREATE TEMP TABLE oiar_001_probe(x integer)")
            cur.execute("INSERT INTO oiar_001_probe VALUES(1)")
            cur.execute("SELECT x FROM oiar_001_probe")
            writable=(cur.fetchone()==(1,))
        conn.rollback()

    return AnalyticsSnapshotFoundationStatus(
        state_table=STATE_TABLE,
        snapshot_table=SNAPSHOT_TABLE,
        state_row_present=state_present,
        database_writable=writable,
        read_only_source_required=True,
        execution_authority=False,
    )

def verify_oiar_001_production_analytics_snapshot_foundation(root=None)->bool:
    status=inspect_foundation(root)
    return (
        status.state_row_present
        and status.database_writable
        and status.read_only_source_required
        and not status.execution_authority
    )
