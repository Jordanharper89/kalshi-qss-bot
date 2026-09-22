from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_007_observation_history import UniversalObservationHistory, verify_observation_history
from .oi_008_observation_source_routing import (
    ObservationRouteDecision,
    verify_observation_source_routing,
)

BUILD_ID = "OI-009"
OI_009_REVISION = "OI_009_OBSERVATION_EVIDENCE_ASSEMBLY_FOUNDATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class ObservationEvidenceAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceObservationRef:
    canonical_observation_id: str
    canonical_observation_hash: str
    source_id: str
    provider: str
    adapter_id: str
    observed_at: datetime
    subject: str
    observation_type: str
    facts: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "facts",
            MappingProxyType(dict(self.facts)),
        )


@dataclass(frozen=True, slots=True)
class ObservationEvidenceBundle:
    query_id: str
    assembled_at: datetime
    route_decision_hash: str
    adapter_ids: tuple[str, ...]
    observations: tuple[EvidenceObservationRef, ...]
    evidence_hash: str
    read_only: bool
    predictive: bool


class ObservationEvidenceAssembler:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def assemble(
        self,
        *,
        query_id: str,
        route_decision: ObservationRouteDecision,
        observations: tuple[CanonicalLiveObservation, ...],
        assembled_at: datetime,
    ) -> ObservationEvidenceBundle:
        if not isinstance(route_decision, ObservationRouteDecision):
            raise TypeError(
                "route_decision must be ObservationRouteDecision"
            )

        query_id = str(query_id).strip()
        if not query_id:
            raise ObservationEvidenceAssemblyError(
                "query_id must not be empty"
            )

        if not isinstance(assembled_at, datetime):
            raise TypeError("assembled_at must be datetime")

        if assembled_at.tzinfo is None:
            raise ObservationEvidenceAssemblyError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(timezone.utc)

        values = tuple(observations)

        if any(
            not isinstance(item, CanonicalLiveObservation)
            for item in values
        ):
            raise TypeError(
                "all observations must be CanonicalLiveObservation"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: (
                    item.observed_at,
                    item.canonical_observation_id,
                ),
            )
        )

        if values != ordered:
            raise ObservationEvidenceAssemblyError(
                "observations must be deterministically sorted"
            )

        allowed_adapters = set(route_decision.adapter_ids)

        if any(
            item.adapter_id not in allowed_adapters
            for item in values
        ):
            raise ObservationEvidenceAssemblyError(
                "observation adapter not authorized by route decision"
            )

        refs = tuple(
            EvidenceObservationRef(
                canonical_observation_id=item.canonical_observation_id,
                canonical_observation_hash=item.canonical_observation_hash,
                source_id=item.source_id,
                provider=item.provider,
                adapter_id=item.adapter_id,
                observed_at=item.observed_at,
                subject=item.subject,
                observation_type=item.observation_type,
                facts=dict(item.facts),
            )
            for item in values
        )

        body = {
            "query_id": query_id,
            "assembled_at": assembled_at,
            "route_decision_hash": route_decision.decision_hash,
            "adapter_ids": route_decision.adapter_ids,
            "observation_hashes": tuple(
                ref.canonical_observation_hash
                for ref in refs
            ),
            "read_only": True,
            "predictive": False,
        }

        return ObservationEvidenceBundle(
            query_id=query_id,
            assembled_at=assembled_at,
            route_decision_hash=route_decision.decision_hash,
            adapter_ids=route_decision.adapter_ids,
            observations=refs,
            evidence_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
        )


def verify_observation_evidence_assembly() -> bool:
    verify_observation_history()
    verify_observation_source_routing()

    if READ_ONLY is not True:
        raise AssertionError("OI-009 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-009 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_009_REVISION",
    "ObservationEvidenceAssemblyError",
    "EvidenceObservationRef",
    "ObservationEvidenceBundle",
    "ObservationEvidenceAssembler",
    "verify_observation_evidence_assembly",
]
