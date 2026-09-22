from __future__ import annotations
from pathlib import Path
from .oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
OPH_020_BUILD_ID="OPH-020"
OPH_020_REVISION="OPH_020_UNIVERSAL_POSTGRESQL_PRODUCER_ADMISSION_V1"

def install_universal_postgresql_ingress(producer,root=None,timeout_seconds=120.0):
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter
    root=Path(root or Path.cwd()).resolve();producer=str(producer);cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    marker="_oph020_universal_postgresql_ingress"
    if getattr(cls,marker,None)==producer:return False
    def queue_only_route(self,observations,routed_at,*args,**kwargs):
        items=tuple(observations)
        if not items:return ()
        priority=100 if "fast_lane" in producer.lower() else 20
        sub=submit_observation_batch(producer,priority,items,root)
        return tuple(await_request(sub.request_id,root,timeout_seconds))
    cls.route_batch=queue_only_route
    setattr(cls,marker,producer)
    setattr(cls,"_oph_direct_canonical_postgresql_write_authority",False)
    return True

def patch_legacy_queue_imports():
    from . import oph_006_durable_cross_process_observation_queue as q
    from . import oph_012_strict_fast_lane_queue_only_admission as f
    from . import oph_013_strict_coverage_queue_only_admission as c
    from .oph_019_postgresql_universal_ingestion_queue import submit_observation_batch as s,await_request as a,claim_next_request,complete_request,fail_request,queue_counts
    q.submit_observation_batch=s;q.await_request=a;q.claim_next_request=claim_next_request;q.complete_request=complete_request;q.fail_request=fail_request;q.queue_counts=queue_counts
    f.submit_observation_batch=s;f.await_request=a;c.submit_observation_batch=s;c.await_request=a
    return True

def verify_oph_020_universal_postgresql_producer_admission():
    return OPH_020_BUILD_ID=="OPH-020" and "POSTGRESQL" in OPH_020_REVISION
