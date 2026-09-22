from __future__ import annotations
from dataclasses import dataclass

from .oar_011_live_observation_admission import (
    LiveObservationAdmissionResult,
)

BUILD_ID = "OAR-013"
OAR_013_REVISION = "OAR_013_OI_CANONICAL_HANDOFF_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class FrozenOICanonicalHandoffRecord:
    iteration_number: int
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    adapter_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    observation_count: int
    frozen_oi_target: str
    read_only: bool


class FrozenOICanonicalHandoff:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def build(
        self,
        admission: LiveObservationAdmissionResult,
    ) -> FrozenOICanonicalHandoffRecord:
        if not isinstance(
            admission,
            LiveObservationAdmissionResult,
        ):
            raise TypeError(
                "admission must be LiveObservationAdmissionResult"
            )

        observations = tuple(
            sorted(
                admission.admitted_observations,
                key=lambda x: x.observation_id,
            )
        )

        return FrozenOICanonicalHandoffRecord(
            iteration_number=admission.iteration_number,
            observation_ids=tuple(
                x.observation_id for x in observations
            ),
            observation_hashes=tuple(
                x.observation_hash for x in observations
            ),
            adapter_ids=tuple(
                sorted({x.adapter_id for x in observations})
            ),
            provider_ids=tuple(
                sorted({x.provider_id for x in observations})
            ),
            capability_ids=tuple(
                sorted({x.capability for x in observations})
            ),
            observation_count=len(observations),
            frozen_oi_target=(
                "OI-003 canonical observation gateway / "
                "frozen Observation Intelligence boundary"
            ),
            read_only=True,
        )


def verify_oi_canonical_handoff() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
