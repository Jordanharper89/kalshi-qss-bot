from __future__ import annotations
from dataclasses import dataclass
from .oar_010_canonical_live_observation_bus import CanonicalLiveObservationBatch

BUILD_ID="OAR-011"
OAR_011_REVISION="OAR_011_LIVE_OBSERVATION_ADMISSION_V1"
READ_ONLY=True
EXECUTION_ALLOWED=False

@dataclass(frozen=True,slots=True)
class LiveObservationAdmissionResult:
    iteration_number:int
    admitted_observations:tuple
    rejected_observation_ids:tuple[str,...]
    duplicate_observation_ids:tuple[str,...]
    admitted_count:int
    rejected_count:int
    read_only:bool

class LiveObservationAdmissionGate:
    read_only=True
    execution_allowed=False
    def admit(self,batch:CanonicalLiveObservationBatch)->LiveObservationAdmissionResult:
        if not isinstance(batch,CanonicalLiveObservationBatch): raise TypeError("batch must be CanonicalLiveObservationBatch")
        seen=set(); admitted=[]; rejected=[]; duplicates=[]
        for obs in batch.observations:
            if obs.observation_hash in seen:
                duplicates.append(obs.observation_id); rejected.append(obs.observation_id); continue
            seen.add(obs.observation_hash)
            if not obs.adapter_id or not obs.provider_id or not obs.capability or not obs.observation_hash:
                rejected.append(obs.observation_id); continue
            admitted.append(obs)
        return LiveObservationAdmissionResult(batch.iteration_number,tuple(admitted),tuple(rejected),tuple(duplicates),len(admitted),len(rejected),True)

def verify_live_observation_admission()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False
    return True
