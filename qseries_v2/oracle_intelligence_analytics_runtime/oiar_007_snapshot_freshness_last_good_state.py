from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, STATE_TABLE
from .oiar_004_indexed_current_cohort_analytics_materializer import ANALYTICS_STAGE

OIAR_007_BUILD_ID="OIAR-007"
OIAR_007_REVISION="OIAR_007_SNAPSHOT_FRESHNESS_LAST_GOOD_STATE_V1"
FRESH_SECONDS=60.0
STALE_SECONDS=300.0

@dataclass(frozen=True)
class AnalyticsSnapshotFreshness:
    snapshot_id:str
    market_count:int
    snapshot_generated_at:str
    last_refresh_completed_at:str
    age_seconds:float
    runtime_status:str
    freshness_status:str
    serves_last_good:bool
    read_only:bool=True
    execution_authority:bool=False

def inspect_snapshot_freshness(root=None,now=None):
    root=Path(root or Path.cwd()).resolve()
    checked=now or datetime.now(timezone.utc)

    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(
                f"SELECT snapshot_id,market_count,generated_at FROM public.{SNAPSHOT_TABLE} "
                "WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",
                (ANALYTICS_STAGE,),
            )
            snap=cur.fetchone()
            cur.execute(
                f"SELECT status,last_completed_at FROM public.{STATE_TABLE} WHERE state_id=1"
            )
            state=cur.fetchone()
        conn.rollback()

    if snap is None:
        raise RuntimeError("OIAR-007 no last-good analytics snapshot available")

    snapshot_id,market_count,generated_at=snap
    runtime_status=str(state[0] if state else "FAILED")
    completed=(state[1] if state and state[1] is not None else generated_at)
    completed=completed.astimezone(timezone.utc)
    age=max(0.0,(checked.astimezone(timezone.utc)-completed).total_seconds())

    if runtime_status in ("DEGRADED","FAILED"):
        freshness="DEGRADED"
    elif age<=FRESH_SECONDS:
        freshness="FRESH"
    elif age<=STALE_SECONDS:
        freshness="STALE"
    else:
        freshness="DEGRADED"

    return AnalyticsSnapshotFreshness(
        str(snapshot_id),
        int(market_count),
        generated_at.astimezone(timezone.utc).isoformat(),
        completed.isoformat(),
        age,
        runtime_status,
        freshness,
        True,
        True,
        False,
    )

def verify_oiar_007_snapshot_freshness(root=None):
    x=inspect_snapshot_freshness(root)
    return bool(
        x.snapshot_id and x.market_count>0 and x.serves_last_good
        and x.read_only and not x.execution_authority
        and x.freshness_status in ("FRESH","STALE","DEGRADED")
    )
