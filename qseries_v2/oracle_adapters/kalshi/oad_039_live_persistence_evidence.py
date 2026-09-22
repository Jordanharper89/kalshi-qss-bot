from dataclasses import dataclass
from types import MappingProxyType

OAD_039_BUILD_ID="OAD-039"
OAD_039_REVISION="OAD_039_END_TO_END_LIVE_PERSISTENCE_EVIDENCE_V1"

@dataclass(frozen=True)
class LivePersistenceEvidence:
    market_events:int
    persisted_observations:int
    observation_ids:tuple[str,...]
    complete:bool
    read_only:bool=True
    execution_authority:bool=False

def build_live_persistence_evidence(observation_ids,market_events):
    ids=tuple(str(x) for x in observation_ids if str(x))
    events=int(market_events)
    if events<0: raise ValueError("non-negative market_events required")
    complete=bool(events>0 and len(ids)==events)
    return LivePersistenceEvidence(events,len(ids),ids,complete,True,False)

def verify_oad_039_end_to_end_live_persistence_evidence():
    x=build_live_persistence_evidence(("a","b","c"),3)
    return x.complete and x.persisted_observations==3 and not x.execution_authority
