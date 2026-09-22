from __future__ import annotations
from dataclasses import dataclass

OPC_031_BUILD_ID="OPC-031"
OPC_031_REVISION="OPC_031_PERSISTENCE_PRIORITY_CONTRACT_V1"

@dataclass(frozen=True)
class PersistencePriority:
    name:str
    rank:int
    blocking_timeout_seconds:float
    microbatch_size:int
    execution_authority:bool=False

FAST_LANE=PersistencePriority("FAST_LANE",100,5.0,1,False)
COVERAGE=PersistencePriority("COVERAGE",20,5.0,25,False)

def priority_for_child(child_name):
    name=str(child_name).strip().lower()
    if name=="fast_lane":
        return FAST_LANE
    if name=="coverage":
        return COVERAGE
    raise ValueError("unsupported persistence child")

def verify_opc_031_persistence_priority_contract():
    return (
        FAST_LANE.rank>COVERAGE.rank
        and FAST_LANE.microbatch_size==1
        and COVERAGE.microbatch_size==25
        and not FAST_LANE.execution_authority
        and not COVERAGE.execution_authority
    )
