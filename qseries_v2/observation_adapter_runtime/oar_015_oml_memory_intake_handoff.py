from __future__ import annotations
from dataclasses import dataclass

from .oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoffRecord,
)
from .oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationRequest,
)

BUILD_ID = "OAR-015"
OAR_015_REVISION = "OAR_015_OML_MEMORY_INTAKE_HANDOFF_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class OMLMemoryIntakeRequest:
    iteration_number: int
    observation_ids: tuple[str, ...]
    observation_hashes: tuple[str, ...]
    provider_ids: tuple[str, ...]
    requires_market_identity_resolution: bool
    requires_evidence_lineage_preservation: bool
    requires_contradiction_preservation: bool
    read_only: bool


class OMLMemoryIntakeHandoff:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def build(
        self,
        *,
        oi_handoff: FrozenOICanonicalHandoffRecord,
        umd_request: UMDMarketCorrelationRequest,
    ) -> OMLMemoryIntakeRequest:
        if not isinstance(
            oi_handoff,
            FrozenOICanonicalHandoffRecord,
        ):
            raise TypeError(
                "oi_handoff must be FrozenOICanonicalHandoffRecord"
            )

        if not isinstance(
            umd_request,
            UMDMarketCorrelationRequest,
        ):
            raise TypeError(
                "umd_request must be UMDMarketCorrelationRequest"
            )

        if (
            oi_handoff.iteration_number
            != umd_request.iteration_number
        ):
            raise ValueError(
                "OI/UMD iteration lineage mismatch"
            )

        if (
            oi_handoff.observation_ids
            != umd_request.observation_ids
        ):
            raise ValueError(
                "OI/UMD observation identity mismatch"
            )

        return OMLMemoryIntakeRequest(
            iteration_number=oi_handoff.iteration_number,
            observation_ids=oi_handoff.observation_ids,
            observation_hashes=oi_handoff.observation_hashes,
            provider_ids=oi_handoff.provider_ids,
            requires_market_identity_resolution=True,
            requires_evidence_lineage_preservation=True,
            requires_contradiction_preservation=True,
            read_only=True,
        )


def verify_oml_memory_intake_handoff() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
