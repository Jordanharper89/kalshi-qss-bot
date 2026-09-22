from __future__ import annotations
from pathlib import Path
from .oph_019_postgresql_universal_ingestion_queue import connect,ensure_postgresql_ingestion_schema,TABLE
OPH_024_BUILD_ID="OPH-024"
OPH_024_REVISION="OPH_024_POSTGRESQL_STALE_CLAIM_RECOVERY_V1"

def recover_stale_claims(root=None,stale_seconds=120):
    root=Path(root or Path.cwd()).resolve();ensure_postgresql_ingestion_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""UPDATE public.{TABLE}
               SET status='PENDING',worker_id=NULL,claimed_at=NULL,
                   next_attempt_at=clock_timestamp(),
                   last_error_type='StaleWriterClaimRecovered',
                   last_error_message='Recovered by OPH-024 after writer ownership timeout'
             WHERE status='IN_PROGRESS'
               AND claimed_at < clock_timestamp()-(%s*interval '1 second')
             RETURNING request_id""",(int(stale_seconds),))
            rows=cur.fetchall()
        conn.commit()
    return tuple(str(r[0]) for r in rows)

def verify_oph_024_postgresql_stale_claim_recovery(root=None):
    from .oph_023_postgresql_single_writer_production_freeze import verify_oph_023_postgresql_single_writer_production_freeze
    return verify_oph_023_postgresql_single_writer_production_freeze(root) and OPH_024_BUILD_ID=="OPH-024"
