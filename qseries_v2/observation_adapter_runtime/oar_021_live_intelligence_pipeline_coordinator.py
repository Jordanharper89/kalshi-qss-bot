from __future__ import annotations

from dataclasses import dataclass

from .oar_011_live_observation_admission import (
    LiveObservationAdmissionResult,
)
from .oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoff,
)
from .oar_018_oi_umd_oml_integration import (
    OIUMDOMLIntegrationBuilder,
    OIUMDOMLIntegrationPackage,
)

BUILD_ID = "OAR-021"
OAR_021_REVISION = "OAR_021_LIVE_INTELLIGENCE_PIPELINE_COORDINATOR_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveIntelligencePipelinePackage:
    iteration_number: int
    observation_count: int
    integration: OIUMDOMLIntegrationPackage
    oi_ready: bool
    umd_ready: bool
    oml_ready: bool
    read_only: bool


class LiveIntelligencePipelineCoordinator:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def coordinate(
        self,
        admission: LiveObservationAdmissionResult,
    ) -> LiveIntelligencePipelinePackage:
        if not isinstance(
            admission,
            LiveObservationAdmissionResult,
        ):
            raise TypeError(
                "admission must be LiveObservationAdmissionResult"
            )

        oi_handoff = (
            FrozenOICanonicalHandoff()
            .build(
                admission
            )
        )

        integration = (
            OIUMDOMLIntegrationBuilder()
            .build(
                oi_handoff
            )
        )

        return LiveIntelligencePipelinePackage(
            iteration_number=(
                admission.iteration_number
            ),
            observation_count=(
                admission.admitted_count
            ),
            integration=integration,
            oi_ready=True,
            umd_ready=True,
            oml_ready=True,
            read_only=True,
        )


def verify_live_intelligence_pipeline_coordinator() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
