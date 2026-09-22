from __future__ import annotations
from pathlib import Path

from .oph_006_durable_cross_process_observation_queue import (
    submit_observation_batch,
    await_request,
)
from .oph_002_priority_observation_ingestion_queue import priority_for_lane
from .oph_011_persistence_provenance_ledger import append_provenance

OPH_013_BUILD_ID="OPH-013"
OPH_013_REVISION="OPH_013_STRICT_COVERAGE_QUEUE_ONLY_ADMISSION_V1"

def install_strict_coverage_queue_only(root=None,timeout_seconds=90.0):
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
        OraclePostgreSQLCanonicalObservationPersistenceRouter,
    )

    root=Path(root or Path.cwd()).resolve()
    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    marker="_oph013_strict_coverage_queue_only"

    if getattr(cls,marker,False):
        return False

    def queue_only_route(self,observations,routed_at,*args,**kwargs):
        items=tuple(observations)
        if not items:
            return ()

        sub=submit_observation_batch(
            "kalshi.coverage",
            priority_for_lane("COVERAGE"),
            items,
            root,
        )

        append_provenance(
            "PRODUCER_SUBMIT",
            root,
            producer="kalshi.coverage",
            request_id=sub.request_id,
            observation_count=len(items),
            direct_postgresql_write_authority=False,
        )

        try:
            result=await_request(
                sub.request_id,
                root,
                timeout_seconds,
            )
        except Exception as exc:
            append_provenance(
                "PRODUCER_FAILURE",
                root,
                producer="kalshi.coverage",
                request_id=sub.request_id,
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                direct_postgresql_write_authority=False,
            )
            raise

        append_provenance(
            "PRODUCER_SUCCESS",
            root,
            producer="kalshi.coverage",
            request_id=sub.request_id,
            observation_count=len(items),
        )

        return tuple(result)

    cls.route_batch=queue_only_route
    setattr(cls,marker,True)
    setattr(cls,"_oph_queue_only_owner","kalshi.coverage")
    return True

def verify_oph_013_strict_coverage_queue_only_admission():
    return priority_for_lane("COVERAGE")==20
