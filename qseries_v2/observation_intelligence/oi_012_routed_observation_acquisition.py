from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Callable, Mapping, Any

from .oi_001_universal_observation_intake import RawObservationEnvelope, deterministic_sha256
from .oi_002_source_adapter_registry import SourceAdapterRegistry
from .oi_003_canonical_observation_gateway import (
    CanonicalLiveObservation,
    CanonicalLiveObservationGateway,
)
from .oi_008_observation_source_routing import (
    ObservationRouteDecision,
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
    verify_observation_source_routing,
)
from .oi_009_observation_evidence_assembly import (
    ObservationEvidenceAssembler,
    ObservationEvidenceBundle,
    verify_observation_evidence_assembly,
)
from .oi_011_multi_source_consensus import verify_multi_source_consensus

BUILD_ID = "OI-012"
OI_012_REVISION = "OI_012_ROUTED_OBSERVATION_ACQUISITION_ENGINE_V1"

READ_ONLY = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class RoutedObservationAcquisitionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AdapterAcquisitionBinding:
    adapter_id: str
    acquire_callable: Callable[[ObservationRouteRequest], tuple[RawObservationEnvelope, ...]]

    def __post_init__(self) -> None:
        adapter_id = str(self.adapter_id).strip().lower()
        if not adapter_id:
            raise RoutedObservationAcquisitionError(
                "adapter_id must not be empty"
            )
        if not callable(self.acquire_callable):
            raise TypeError("acquire_callable must be callable")

        object.__setattr__(self, "adapter_id", adapter_id)


@dataclass(frozen=True, slots=True)
class RoutedObservationAcquisitionResult:
    route_decision: ObservationRouteDecision
    observations: tuple[CanonicalLiveObservation, ...]
    evidence_bundle: ObservationEvidenceBundle
    invoked_adapter_ids: tuple[str, ...]
    acquisition_hash: str


class RoutedObservationAcquisitionEngine:
    read_only = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        *,
        adapter_registry: SourceAdapterRegistry,
        routing_registry: ObservationSourceRoutingRegistry,
        bindings: tuple[AdapterAcquisitionBinding, ...],
    ) -> None:
        if not isinstance(adapter_registry, SourceAdapterRegistry):
            raise TypeError("adapter_registry must be SourceAdapterRegistry")

        if not isinstance(routing_registry, ObservationSourceRoutingRegistry):
            raise TypeError(
                "routing_registry must be ObservationSourceRoutingRegistry"
            )

        values = tuple(bindings)

        if any(
            not isinstance(item, AdapterAcquisitionBinding)
            for item in values
        ):
            raise TypeError(
                "all bindings must be AdapterAcquisitionBinding"
            )

        ordered = tuple(
            sorted(values, key=lambda item: item.adapter_id)
        )

        if values != ordered:
            raise RoutedObservationAcquisitionError(
                "bindings must be deterministically sorted"
            )

        ids = tuple(item.adapter_id for item in values)
        if len(ids) != len(set(ids)):
            raise RoutedObservationAcquisitionError(
                "duplicate adapter binding"
            )

        for adapter_id in ids:
            if adapter_registry.get(adapter_id) is None:
                raise RoutedObservationAcquisitionError(
                    f"binding references unknown adapter: {adapter_id}"
                )

        self._adapter_registry = adapter_registry
        self._routing_registry = routing_registry
        self._bindings = MappingProxyType(
            {item.adapter_id: item for item in values}
        )
        self._gateway = CanonicalLiveObservationGateway(
            adapter_registry
        )
        self._assembler = ObservationEvidenceAssembler()

    def acquire(
        self,
        *,
        query_id: str,
        request: ObservationRouteRequest,
        assembled_at: datetime,
    ) -> RoutedObservationAcquisitionResult:
        if not isinstance(request, ObservationRouteRequest):
            raise TypeError("request must be ObservationRouteRequest")

        if not isinstance(assembled_at, datetime):
            raise TypeError("assembled_at must be datetime")

        if assembled_at.tzinfo is None:
            raise RoutedObservationAcquisitionError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(timezone.utc)

        decision = self._routing_registry.route(request)

        observations: list[CanonicalLiveObservation] = []
        invoked = []

        for adapter_id in decision.adapter_ids:
            binding = self._bindings.get(adapter_id)

            if binding is None:
                raise RoutedObservationAcquisitionError(
                    f"missing acquisition binding for routed adapter: {adapter_id}"
                )

            envelopes = tuple(
                binding.acquire_callable(request)
            )

            if any(
                not isinstance(item, RawObservationEnvelope)
                for item in envelopes
            ):
                raise RoutedObservationAcquisitionError(
                    f"adapter {adapter_id} returned invalid envelope"
                )

            for envelope in envelopes:
                if envelope.source.adapter_id != adapter_id:
                    raise RoutedObservationAcquisitionError(
                        "adapter binding returned envelope owned by different adapter"
                    )

                observations.append(
                    self._gateway.canonicalize(
                        envelope
                    ).canonical_observation
                )

            invoked.append(adapter_id)

        canonical = tuple(
            sorted(
                observations,
                key=lambda item: (
                    item.observed_at,
                    item.canonical_observation_id,
                ),
            )
        )

        bundle = self._assembler.assemble(
            query_id=query_id,
            route_decision=decision,
            observations=canonical,
            assembled_at=assembled_at,
        )

        body = {
            "query_id": query_id,
            "route_decision_hash": decision.decision_hash,
            "invoked_adapter_ids": tuple(invoked),
            "observation_hashes": tuple(
                item.canonical_observation_hash
                for item in canonical
            ),
            "evidence_hash": bundle.evidence_hash,
        }

        return RoutedObservationAcquisitionResult(
            route_decision=decision,
            observations=canonical,
            evidence_bundle=bundle,
            invoked_adapter_ids=tuple(invoked),
            acquisition_hash=deterministic_sha256(body),
        )


def verify_routed_observation_acquisition() -> bool:
    verify_observation_source_routing()
    verify_observation_evidence_assembly()
    verify_multi_source_consensus()

    if READ_ONLY is not True:
        raise AssertionError("OI-012 must remain read-only")

    if any(
        (
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-012 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_012_REVISION",
    "RoutedObservationAcquisitionError",
    "AdapterAcquisitionBinding",
    "RoutedObservationAcquisitionResult",
    "RoutedObservationAcquisitionEngine",
    "verify_routed_observation_acquisition",
]
