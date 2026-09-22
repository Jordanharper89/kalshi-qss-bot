from __future__ import annotations
from pathlib import Path
from .oph_006_durable_cross_process_observation_queue import submit_observation_batch,await_request
from .oph_002_priority_observation_ingestion_queue import priority_for_lane

OPH_008_BUILD_ID="OPH-008"
OPH_008_REVISION="OPH_008_FAST_LANE_QUEUE_MIGRATION_V1"

def install_fast_lane_queue_migration(root=None,timeout_seconds=30.0):
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter
    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    marker="_oph008_fast_lane_queue_migration"
    if getattr(cls,marker,False): return False
    root=Path(root or Path.cwd()).resolve()
    original=cls.route_batch
    def queued_route(self,observations,routed_at,*args,**kwargs):
        items=tuple(observations)
        if not items: return original(self,items,routed_at,*args,**kwargs)
        sub=submit_observation_batch("kalshi.fast_lane",priority_for_lane("FAST_LANE"),items,root)
        return await_request(sub.request_id,root,timeout_seconds)
    cls.route_batch=queued_route
    setattr(cls,"_oph008_original_route_batch",original)
    setattr(cls,marker,True)
    return True

def verify_oph_008_fast_lane_queue_migration():
    return priority_for_lane("FAST_LANE")==100
