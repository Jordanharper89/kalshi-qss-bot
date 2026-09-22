from __future__ import annotations
from pathlib import Path

from .opr_001_persistent_queue_session import PersistentQueueSession

OPR_002_BUILD_ID="OPR-002"
OPR_002_REVISION="OPR_002_PERSISTENT_PRODUCER_INGRESS_V1"

_SESSIONS={}

def producer_session(producer,root=None):
    root=Path(root or Path.cwd()).resolve()
    key=(str(producer),str(root))
    session=_SESSIONS.get(key)
    if session is None:
        session=PersistentQueueSession(root,autocommit=True)
        session.open()
        _SESSIONS[key]=session
    return session

def install_persistent_postgresql_ingress(producer,root=None,timeout_seconds=120.0,poll_seconds=0.025):
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
        OraclePostgreSQLCanonicalObservationPersistenceRouter,
    )
    root=Path(root or Path.cwd()).resolve()
    producer=str(producer)
    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    marker="_opr002_persistent_postgresql_ingress"
    if getattr(cls,marker,None)==producer:return False
    session=producer_session(producer,root)

    def queue_only_route(self,observations,routed_at,*args,**kwargs):
        items=tuple(observations)
        if not items:return ()
        priority=100 if "fast_lane" in producer.lower() else 20
        sub=session.submit(producer,priority,items)
        return tuple(session.await_result(
            sub.request_id,timeout_seconds=timeout_seconds,poll_seconds=poll_seconds
        ))

    cls.route_batch=queue_only_route
    setattr(cls,marker,producer)
    setattr(cls,"_opr_queue_session",session)
    setattr(cls,"_oph_direct_canonical_postgresql_write_authority",False)
    return True

def verify_opr_002_persistent_producer_ingress(root=None):
    return OPR_002_BUILD_ID=="OPR-002" and callable(install_persistent_postgresql_ingress)
