from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_002_source_adapter_registry import SourceAdapterRegistry
from .oi_027_generic_observation_router_interface import (
    GenericObservationNeed,
    GenericObservationRouterInterface,
)

BUILD_ID = "OI-028"
OI_028_REVISION = "OI_028_ADAPTER_CAPABILITY_COVERAGE_REGISTRY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class AdapterCapabilityCoverageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AdapterCoverageRecord:
    need_id: str
    domain: str
    entity_kind: str
    observation_type: str
    subject_hint: str
    covered: bool
    adapter_ids: tuple[str, ...]
    coverage_hash: str


class AdapterCapabilityCoverageRegistry:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def __init__(
        self,
        *,
        adapter_registry: SourceAdapterRegistry,
        router: GenericObservationRouterInterface,
    ) -> None:
        if not isinstance(adapter_registry, SourceAdapterRegistry):
            raise TypeError(
                "adapter_registry must be SourceAdapterRegistry"
            )
        if not isinstance(router, GenericObservationRouterInterface):
            raise TypeError(
                "router must be GenericObservationRouterInterface"
            )

        self._adapter_registry = adapter_registry
        self._router = router

    def evaluate_need(
        self,
        need: GenericObservationNeed,
    ) -> AdapterCoverageRecord:
        if not isinstance(need, GenericObservationNeed):
            raise TypeError("need must be GenericObservationNeed")

        route = self._router.route_need(need)

        enabled_adapter_ids = tuple(
            adapter_id
            for adapter_id in route.route_decision.adapter_ids
            if (
                self._adapter_registry.get(adapter_id) is not None
                and self._adapter_registry.get(adapter_id).enabled_for_intake
            )
        )

        covered = bool(enabled_adapter_ids)

        body = {
            "need_id": need.need_id,
            "domain": need.domain,
            "entity_kind": need.entity_kind,
            "observation_type": need.observation_type,
            "subject_hint": need.subject_hint,
            "covered": covered,
            "adapter_ids": enabled_adapter_ids,
        }

        return AdapterCoverageRecord(
            need_id=need.need_id,
            domain=need.domain,
            entity_kind=need.entity_kind,
            observation_type=need.observation_type,
            subject_hint=need.subject_hint,
            covered=covered,
            adapter_ids=enabled_adapter_ids,
            coverage_hash=deterministic_sha256(body),
        )

    def evaluate_many(
        self,
        needs: tuple[GenericObservationNeed, ...],
    ) -> tuple[AdapterCoverageRecord, ...]:
        values = tuple(needs)

        if any(
            not isinstance(item, GenericObservationNeed)
            for item in values
        ):
            raise TypeError(
                "all needs must be GenericObservationNeed"
            )

        ids = tuple(item.need_id for item in values)

        if len(ids) != len(set(ids)):
            raise AdapterCapabilityCoverageError(
                "duplicate need_id"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: item.need_id,
            )
        )

        if values != ordered:
            raise AdapterCapabilityCoverageError(
                "needs must be deterministically sorted"
            )

        return tuple(
            self.evaluate_need(item)
            for item in values
        )

    def coverage_summary(
        self,
        needs: tuple[GenericObservationNeed, ...],
    ) -> MappingProxyType:
        records = self.evaluate_many(needs)

        covered = tuple(
            item.need_id
            for item in records
            if item.covered
        )

        missing = tuple(
            item.need_id
            for item in records
            if not item.covered
        )

        return MappingProxyType(
            {
                "total": len(records),
                "covered": len(covered),
                "missing": len(missing),
                "covered_need_ids": covered,
                "missing_need_ids": missing,
                "coverage_hash": deterministic_sha256(
                    tuple(
                        item.coverage_hash
                        for item in records
                    )
                ),
            }
        )


def verify_adapter_capability_coverage() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-028 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-028 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_028_REVISION",
    "AdapterCapabilityCoverageError",
    "AdapterCoverageRecord",
    "AdapterCapabilityCoverageRegistry",
    "verify_adapter_capability_coverage",
]
