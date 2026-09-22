from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import STATE_TABLE
from .oiar_002_current_reasoning_market_cohort_snapshot import materialize_current_reasoning_market_cohort
from .oiar_004_indexed_current_cohort_analytics_materializer import materialize_indexed_current_cohort_analytics

OIAR_006_BUILD_ID="OIAR-006"
OIAR_006_REVISION="OIAR_006_CONTINUOUS_ANALYTICS_REFRESH_RUNTIME_V1"
DEFAULT_CADENCE_SECONDS=15.0

@dataclass(frozen=True)
class AnalyticsRefreshCycle:
    status:str
    cohort_markets:int
    analytics_markets:int
    learner_state_hash:str
    elapsed_seconds:float
    completed_at:str
    execution_authority:bool=False

def _update_state(root,status,error_type=None,error_message=None):
    now=datetime.now(timezone.utc)
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:
            if status=="RUNNING":
                cur.execute(
                    f"UPDATE public.{STATE_TABLE} SET status='RUNNING',last_started_at=%s,last_error_type=NULL,last_error_message=NULL,updated_at=clock_timestamp() WHERE state_id=1",
                    (now,),
                )
            elif status=="IDLE":
                cur.execute(
                    f"UPDATE public.{STATE_TABLE} SET status='IDLE',last_completed_at=%s,last_error_type=NULL,last_error_message=NULL,updated_at=clock_timestamp() WHERE state_id=1",
                    (now,),
                )
            else:
                cur.execute(
                    f"UPDATE public.{STATE_TABLE} SET status='DEGRADED',last_completed_at=%s,failure_count=failure_count+1,last_error_type=%s,last_error_message=%s,updated_at=clock_timestamp() WHERE state_id=1",
                    (now,str(error_type or "RuntimeError"),str(error_message or "")[:1000]),
                )

def run_refresh_cycle(root=None):
    root=Path(root or Path.cwd()).resolve()
    started=time.monotonic()
    _update_state(root,"RUNNING")
    try:
        cohort=materialize_current_reasoning_market_cohort(root)
        analytics=materialize_indexed_current_cohort_analytics(
            root,
            per_market=250,
            timeout_ms=15000,
        )
        elapsed=time.monotonic()-started
        completed=datetime.now(timezone.utc)
        _update_state(root,"IDLE")
        return AnalyticsRefreshCycle(
            "IDLE",
            int(cohort.market_count),
            int(analytics["analytics_market_count"]),
            str(analytics.get("learner_state_hash") or cohort.learner_state_hash),
            elapsed,
            completed.isoformat(),
            False,
        )
    except Exception as exc:
        _update_state(root,"DEGRADED",type(exc).__name__,str(exc))
        raise
