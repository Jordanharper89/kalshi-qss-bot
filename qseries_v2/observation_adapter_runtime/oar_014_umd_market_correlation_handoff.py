from __future__ import annotations
from dataclasses import dataclass

from .oar_013_oi_canonical_handoff import (
    FrozenOICanonicalHandoffRecord,
)

BUILD_ID = "OAR-014"
OAR_014_REVISION = "OAR_014_UMD_MARKET_CORRELATION_HANDOFF_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class UMDMarketCorrelationRequest:
    iteration_number: int
    observation_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    market_identity_required: bool
    related_market_resolution_required: bool
    read_only: bool


class UMDMarketCorrelationHandoff:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def build(
        self,
        oi_handoff: FrozenOICanonicalHandoffRecord,
    ) -> UMDMarketCorrelationRequest:
        if not isinstance(
            oi_handoff,
            FrozenOICanonicalHandoffRecord,
        ):
            raise TypeError(
                "oi_handoff must be FrozenOICanonicalHandoffRecord"
            )

        return UMDMarketCorrelationRequest(
            iteration_number=oi_handoff.iteration_number,
            observation_ids=oi_handoff.observation_ids,
            provider_ids=oi_handoff.provider_ids,
            capability_ids=oi_handoff.capability_ids,
            market_identity_required=True,
            related_market_resolution_required=True,
            read_only=True,
        )


def verify_umd_market_correlation_handoff() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
