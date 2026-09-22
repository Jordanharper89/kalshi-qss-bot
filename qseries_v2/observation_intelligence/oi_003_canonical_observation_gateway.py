from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

from .oi_001_universal_observation_intake import (
    RawObservationEnvelope,
    UniversalObservationIntake,
    deterministic_sha256,
    verify_universal_observation_intake,
)

from .oi_002_source_adapter_registry import (
    SourceAdapterRegistry,
    verify_source_adapter_registry,
)


BUILD_ID = "OI-003"

OI_003_REVISION = (
    "OI_003_CANONICAL_LIVE_OBSERVATION_GATEWAY_V1"
)

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class CanonicalObservationGatewayError(
    ValueError
):
    pass


@dataclass(frozen=True, slots=True)
class CanonicalLiveObservation:
    canonical_observation_id: str
    source_id: str
    source_kind: str
    provider: str
    adapter_id: str
    external_observation_id: str
    observed_at: datetime
    subject: str
    observation_type: str
    facts: Mapping[str, Any]
    metadata: Mapping[str, Any]
    source_hash: str
    raw_envelope_hash: str
    canonical_observation_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "facts",
            MappingProxyType(
                dict(self.facts)
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@dataclass(frozen=True, slots=True)
class CanonicalObservationGatewayReceipt:
    canonical_observation: (
        CanonicalLiveObservation
    )
    adapter_registry_hash: str
    intake_receipt_hash: str


class CanonicalLiveObservationGateway:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False

    def __init__(
        self,
        registry: SourceAdapterRegistry,
    ) -> None:
        if not isinstance(
            registry,
            SourceAdapterRegistry,
        ):
            raise TypeError(
                "registry must be SourceAdapterRegistry"
            )

        self._registry = registry
        self._intake = (
            UniversalObservationIntake()
        )

    def canonicalize(
        self,
        envelope: RawObservationEnvelope,
    ) -> CanonicalObservationGatewayReceipt:
        if not isinstance(
            envelope,
            RawObservationEnvelope,
        ):
            raise TypeError(
                "envelope must be RawObservationEnvelope"
            )

        descriptor = self._registry.get(
            envelope.source.adapter_id
        )

        if descriptor is None:
            raise CanonicalObservationGatewayError(
                "source adapter is not registered"
            )

        if descriptor.enabled_for_intake is not True:
            raise CanonicalObservationGatewayError(
                "source adapter is not enabled for intake"
            )

        if (
            descriptor.source_id
            != envelope.source.source_id
        ):
            raise CanonicalObservationGatewayError(
                "source_id does not match registered adapter"
            )

        if (
            descriptor.source_kind
            != envelope.source.source_kind
        ):
            raise CanonicalObservationGatewayError(
                "source_kind does not match registered adapter"
            )

        intake_receipt = (
            self._intake.accept(
                envelope
            )
        )

        if intake_receipt.accepted is not True:
            raise CanonicalObservationGatewayError(
                "observation intake rejected envelope"
            )

        identity_material = {
            "source_id": (
                envelope.source.source_id
            ),
            "adapter_id": (
                envelope.source.adapter_id
            ),
            "external_observation_id": (
                envelope.external_observation_id
            ),
            "observed_at": (
                envelope.observed_at
            ),
            "subject": (
                envelope.subject
            ),
            "observation_type": (
                envelope.observation_type
            ),
        }

        identity_hash = deterministic_sha256(
            identity_material
        )

        canonical_observation_id = (
            "obs."
            + identity_hash
        )

        body = {
            "canonical_observation_id": (
                canonical_observation_id
            ),
            "source_id": (
                envelope.source.source_id
            ),
            "source_kind": (
                envelope.source.source_kind
            ),
            "provider": (
                envelope.source.provider
            ),
            "adapter_id": (
                envelope.source.adapter_id
            ),
            "external_observation_id": (
                envelope.external_observation_id
            ),
            "observed_at": (
                envelope.observed_at
            ),
            "subject": (
                envelope.subject
            ),
            "observation_type": (
                envelope.observation_type
            ),
            "facts": dict(
                envelope.payload
            ),
            "metadata": dict(
                envelope.metadata
            ),
            "source_hash": (
                envelope.source.source_hash
            ),
            "raw_envelope_hash": (
                envelope.envelope_hash
            ),
        }

        observation_hash = (
            deterministic_sha256(
                body
            )
        )

        observation = (
            CanonicalLiveObservation(
                **body,
                canonical_observation_hash=(
                    observation_hash
                ),
            )
        )

        intake_receipt_hash = (
            deterministic_sha256(
                {
                    "envelope_hash": (
                        intake_receipt.envelope_hash
                    ),
                    "source_hash": (
                        intake_receipt.source_hash
                    ),
                    "accepted": (
                        intake_receipt.accepted
                    ),
                    "reason_codes": (
                        intake_receipt.reason_codes
                    ),
                }
            )
        )

        return (
            CanonicalObservationGatewayReceipt(
                canonical_observation=(
                    observation
                ),
                adapter_registry_hash=(
                    self._registry.registry_hash
                ),
                intake_receipt_hash=(
                    intake_receipt_hash
                ),
            )
        )


def verify_canonical_observation_gateway() -> bool:
    verify_universal_observation_intake()
    verify_source_adapter_registry()

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-003 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_003_REVISION",
    "CanonicalObservationGatewayError",
    "CanonicalLiveObservation",
    "CanonicalObservationGatewayReceipt",
    "CanonicalLiveObservationGateway",
    "verify_canonical_observation_gateway",
]
