from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_013_observation_requirement_resolution import (
    ObservationRequirementResolver,
)
from .oi_027_generic_observation_router_interface import (
    GenericObservationNeed,
)
from .oi_028_adapter_capability_coverage import (
    AdapterCapabilityCoverageRegistry,
)

BUILD_ID = "OI-029"
OI_029_REVISION = "OI_029_OBSERVATION_ACQUISITION_PLAN_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class ObservationAcquisitionPlanError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationAcquisitionPlanItem:
    ordinal: int
    need_id: str
    domain: str
    entity_kind: str
    observation_type: str
    subject_hint: str
    adapter_ids: tuple[str, ...]
    covered: bool
    item_hash: str


@dataclass(frozen=True, slots=True)
class ObservationAcquisitionPlan:
    plan_id: str
    profile_id: str
    subject_hint: str
    items: tuple[ObservationAcquisitionPlanItem, ...]
    covered_count: int
    missing_count: int
    complete_coverage: bool
    plan_hash: str
    read_only: bool


class ObservationAcquisitionPlanBuilder:
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
        resolver: ObservationRequirementResolver,
        coverage_registry: AdapterCapabilityCoverageRegistry,
    ) -> None:
        if not isinstance(
            resolver,
            ObservationRequirementResolver,
        ):
            raise TypeError(
                "resolver must be ObservationRequirementResolver"
            )

        if not isinstance(
            coverage_registry,
            AdapterCapabilityCoverageRegistry,
        ):
            raise TypeError(
                "coverage_registry must be AdapterCapabilityCoverageRegistry"
            )

        self._resolver = resolver
        self._coverage = coverage_registry

    def build(
        self,
        *,
        plan_id: str,
        profile_id: str,
        subject_hint: str,
    ) -> ObservationAcquisitionPlan:
        plan_id_value = str(plan_id).strip()
        profile_id_value = " ".join(
            str(profile_id).strip().lower().split()
        )
        subject_value = " ".join(
            str(subject_hint).strip().split()
        )

        if not plan_id_value:
            raise ObservationAcquisitionPlanError(
                "plan_id must not be empty"
            )

        if not profile_id_value:
            raise ObservationAcquisitionPlanError(
                "profile_id must not be empty"
            )

        if not subject_value:
            raise ObservationAcquisitionPlanError(
                "subject_hint must not be empty"
            )

        requests = self._resolver.required_requests(
            profile_id_value
        )

        items = []

        for ordinal, request in enumerate(
            requests,
            start=1,
        ):
            need = GenericObservationNeed(
                need_id=(
                    f"{profile_id_value}.need.{ordinal}"
                ),
                domain=request.domain,
                entity_kind=request.entity_kind,
                observation_type=request.observation_type,
                subject_hint=subject_value,
            )

            coverage = self._coverage.evaluate_need(
                need
            )

            body = {
                "ordinal": ordinal,
                "need_id": need.need_id,
                "domain": need.domain,
                "entity_kind": need.entity_kind,
                "observation_type": need.observation_type,
                "subject_hint": need.subject_hint,
                "adapter_ids": coverage.adapter_ids,
                "covered": coverage.covered,
            }

            items.append(
                ObservationAcquisitionPlanItem(
                    ordinal=ordinal,
                    need_id=need.need_id,
                    domain=need.domain,
                    entity_kind=need.entity_kind,
                    observation_type=need.observation_type,
                    subject_hint=need.subject_hint,
                    adapter_ids=coverage.adapter_ids,
                    covered=coverage.covered,
                    item_hash=deterministic_sha256(body),
                )
            )

        covered_count = sum(
            1
            for item in items
            if item.covered
        )

        missing_count = len(items) - covered_count
        complete_coverage = missing_count == 0

        body = {
            "plan_id": plan_id_value,
            "profile_id": profile_id_value,
            "subject_hint": subject_value,
            "item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "covered_count": covered_count,
            "missing_count": missing_count,
            "complete_coverage": complete_coverage,
            "read_only": True,
        }

        return ObservationAcquisitionPlan(
            plan_id=plan_id_value,
            profile_id=profile_id_value,
            subject_hint=subject_value,
            items=tuple(items),
            covered_count=covered_count,
            missing_count=missing_count,
            complete_coverage=complete_coverage,
            plan_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_observation_acquisition_plan() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-029 must remain read-only"
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
            "OI-029 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_029_REVISION",
    "ObservationAcquisitionPlanError",
    "ObservationAcquisitionPlanItem",
    "ObservationAcquisitionPlan",
    "ObservationAcquisitionPlanBuilder",
    "verify_observation_acquisition_plan",
]
