from __future__ import annotations
from pathlib import Path

from .oph_006_durable_cross_process_observation_queue import (
    submit_observation_batch,
    await_request,
)
from .oph_002_priority_observation_ingestion_queue import priority_for_lane
from .oph_011_persistence_provenance_ledger import append_provenance

OPH_012_BUILD_ID="OPH-012"
OPH_012_REVISION="OPH_012_STRICT_FAST_LANE_QUEUE_ONLY_ADMISSION_V1"

def install_strict_fast_lane_queue_only(root=None,timeout_seconds=45.0):
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
        OraclePostgreSQLCanonicalObservationPersistenceRouter,
    )

    root=Path(root or Path.cwd()).resolve()
    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    marker="_oph012_strict_fast_lane_queue_only"

    if getattr(cls,marker,False):
        return False

    def queue_only_route(self,observations,routed_at,*args,**kwargs):
        items=tuple(observations)
        if not items:
            return ()

        sub=submit_observation_batch(
            "kalshi.fast_lane",
            priority_for_lane("FAST_LANE"),
            items,
            root,
        )

        append_provenance(
            "PRODUCER_SUBMIT",
            root,
            producer="kalshi.fast_lane",
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
                producer="kalshi.fast_lane",
                request_id=sub.request_id,
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                direct_postgresql_write_authority=False,
            )
            raise

        append_provenance(
            "PRODUCER_SUCCESS",
            root,
            producer="kalshi.fast_lane",
            request_id=sub.request_id,
            observation_count=len(items),
        )

        return tuple(result)

    cls.route_batch=queue_only_route
    setattr(cls,marker,True)
    setattr(cls,"_oph_queue_only_owner","kalshi.fast_lane")
    return True

def verify_oph_012_strict_fast_lane_queue_only_admission():
    return priority_for_lane("FAST_LANE")==100
