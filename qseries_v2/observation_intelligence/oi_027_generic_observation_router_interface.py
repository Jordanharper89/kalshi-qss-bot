from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_008_observation_source_routing import (
    ObservationRouteDecision,
    ObservationRouteRequest,
    ObservationSourceRoutingRegistry,
)
from .oi_013_observation_requirement_resolution import (
    ObservationRequirementResolver,
)

BUILD_ID = "OI-027"
OI_027_REVISION = "OI_027_GENERIC_OBSERVATION_ROUTER_INTERFACE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class GenericObservationRouterInterfaceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class GenericObservationNeed:
    need_id: str
    domain: str
    entity_kind: str
    observation_type: str
    subject_hint: str

    def __post_init__(self) -> None:
        for field in (
            "need_id",
            "domain",
            "entity_kind",
            "observation_type",
            "subject_hint",
        ):
            value = " ".join(
                str(getattr(self, field)).strip().split()
            )

            if not value:
                raise GenericObservationRouterInterfaceError(
                    f"{field} must not be empty"
                )

            if field != "subject_hint":
                value = value.lower()

            object.__setattr__(
                self,
                field,
                value,
            )


@dataclass(frozen=True, slots=True)
class GenericObservationRoute:
    need: GenericObservationNeed
    route_decision: ObservationRouteDecision
    route_hash: str


class GenericObservationRouterInterface:
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
        routing_registry: ObservationSourceRoutingRegistry,
    ) -> None:
        if not isinstance(
            routing_registry,
            ObservationSourceRoutingRegistry,
        ):
            raise TypeError(
                "routing_registry must be ObservationSourceRoutingRegistry"
            )

        self._routing_registry = routing_registry

    def route_need(
        self,
        need: GenericObservationNeed,
    ) -> GenericObservationRoute:
        if not isinstance(
            need,
            GenericObservationNeed,
        ):
            raise TypeError(
                "need must be GenericObservationNeed"
            )

        request = ObservationRouteRequest(
            domain=need.domain,
            entity_kind=need.entity_kind,
            observation_type=need.observation_type,
        )

        decision = self._routing_registry.route(
            request
        )

        body = {
            "need_id": need.need_id,
            "domain": need.domain,
            "entity_kind": need.entity_kind,
            "observation_type": need.observation_type,
            "subject_hint": need.subject_hint,
            "decision_hash": decision.decision_hash,
            "adapter_ids": decision.adapter_ids,
        }

        return GenericObservationRoute(
            need=need,
            route_decision=decision,
            route_hash=deterministic_sha256(body),
        )

    def route_profile(
        self,
        *,
        profile_id: str,
        resolver: ObservationRequirementResolver,
        subject_hint: str,
    ) -> tuple[GenericObservationRoute, ...]:
        if not isinstance(
            resolver,
            ObservationRequirementResolver,
        ):
            raise TypeError(
                "resolver must be ObservationRequirementResolver"
            )

        requests = resolver.required_requests(
            profile_id
        )

        routes = []

        for index, request in enumerate(
            requests,
            start=1,
        ):
            need = GenericObservationNeed(
                need_id=(
                    f"{str(profile_id).strip().lower()}."
                    f"need.{index}"
                ),
                domain=request.domain,
                entity_kind=request.entity_kind,
                observation_type=request.observation_type,
                subject_hint=subject_hint,
            )

            routes.append(
                self.route_need(
                    need
                )
            )

        return tuple(routes)


def verify_generic_observation_router_interface() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-027 must remain read-only"
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
            "OI-027 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_027_REVISION",
    "GenericObservationRouterInterfaceError",
    "GenericObservationNeed",
    "GenericObservationRoute",
    "GenericObservationRouterInterface",
    "verify_generic_observation_router_interface",
]
