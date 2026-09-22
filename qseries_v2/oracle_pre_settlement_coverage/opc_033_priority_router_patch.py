from __future__ import annotations
from pathlib import Path

from .opc_031_persistence_priority_contract import priority_for_child
from .opc_032_cross_process_persistence_arbiter import acquire_persistence_lease

OPC_033_BUILD_ID="OPC-033"
OPC_033_REVISION="OPC_033_PRIORITY_ROUTER_PATCH_V1"

_PATCH_MARKER="_opc_priority_arbitration_v1"

def install_priority_router_patch(child_name,root=None):
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
        OraclePostgreSQLCanonicalObservationPersistenceRouter,
    )

    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    if getattr(cls,_PATCH_MARKER,False):
        return False

    policy=priority_for_child(child_name)
    original=cls.route_batch
    root=Path(root or Path.cwd()).resolve()

    def route_batch_with_priority(self,observations,routed_at,*args,**kwargs):
        items=tuple(observations)
        if not items:
            return original(self,items,routed_at,*args,**kwargs)

        if policy.name=="FAST_LANE":
            with acquire_persistence_lease(
                policy.name,
                root=root,
                timeout_seconds=policy.blocking_timeout_seconds,
            ):
                return original(self,items,routed_at,*args,**kwargs)

        evidence=[]
        size=max(1,int(policy.microbatch_size))

        for start in range(0,len(items),size):
            chunk=items[start:start+size]
            with acquire_persistence_lease(
                policy.name,
                root=root,
                timeout_seconds=policy.blocking_timeout_seconds,
            ):
                result=original(self,chunk,routed_at,*args,**kwargs)
                evidence.extend(tuple(result))

        return tuple(evidence)

    setattr(cls,"_opc_priority_original_route_batch",original)
    setattr(cls,"route_batch",route_batch_with_priority)
    setattr(cls,_PATCH_MARKER,True)
    setattr(cls,"_opc_priority_child",str(child_name))
    return True

def verify_opc_033_priority_router_patch():
    from .opc_031_persistence_priority_contract import FAST_LANE,COVERAGE
    return (
        FAST_LANE.rank>COVERAGE.rank
        and COVERAGE.microbatch_size==25
        and FAST_LANE.microbatch_size==1
    )
