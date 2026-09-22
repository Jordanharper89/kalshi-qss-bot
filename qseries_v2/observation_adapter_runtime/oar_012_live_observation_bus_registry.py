from __future__ import annotations
from dataclasses import dataclass
from .oar_011_live_observation_admission import LiveObservationAdmissionResult

BUILD_ID="OAR-012"
OAR_012_REVISION="OAR_012_LIVE_OBSERVATION_BUS_REGISTRY_V1"
READ_ONLY=True
EXECUTION_ALLOWED=False
PERSISTENCE_ALLOWED=False

@dataclass(frozen=True,slots=True)
class LiveObservationBusSnapshot:
    iteration_number:int
    observation_ids:tuple[str,...]
    adapter_ids:tuple[str,...]
    provider_ids:tuple[str,...]
    capability_ids:tuple[str,...]
    observation_count:int
    read_only:bool

class LiveObservationBusRegistry:
    read_only=True
    execution_allowed=False
    persistence_allowed=False
    def build_snapshot(self,admission:LiveObservationAdmissionResult)->LiveObservationBusSnapshot:
        if not isinstance(admission,LiveObservationAdmissionResult): raise TypeError("admission must be LiveObservationAdmissionResult")
        observations=tuple(sorted(admission.admitted_observations,key=lambda x:x.observation_id))
        return LiveObservationBusSnapshot(
            admission.iteration_number,
            tuple(x.observation_id for x in observations),
            tuple(sorted({x.adapter_id for x in observations})),
            tuple(sorted({x.provider_id for x in observations})),
            tuple(sorted({x.capability for x in observations})),
            len(observations),
            True,
        )

def verify_live_observation_bus_registry()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and PERSISTENCE_ALLOWED is False
    return True
