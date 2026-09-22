from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_008_observation_source_routing import ObservationRouteRequest
from .oi_012_routed_observation_acquisition import (
    RoutedObservationAcquisitionEngine,
    RoutedObservationAcquisitionResult,
)
from .oi_029_observation_acquisition_plan import ObservationAcquisitionPlan
from .oi_030_oracle_observation_request_package import (
    OracleObservationRequestPackage,
)

BUILD_ID = "OI-031"
OI_031_REVISION = "OI_031_ORACLE_OBSERVATION_REQUEST_DISPATCHER_V1"

READ_ONLY = True
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class OracleObservationRequestDispatcherError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DispatchedObservationNeed:
    ordinal: int
    need_id: str
    covered: bool
    adapter_ids: tuple[str, ...]
    acquisition_hash: str | None
    observation_count: int
    evidence_hash: str | None
    dispatch_item_hash: str


@dataclass(frozen=True, slots=True)
class OracleObservationDispatchResult:
    request_id: str
    request_package_hash: str
    plan_hash: str
    dispatched_at: datetime
    items: tuple[DispatchedObservationNeed, ...]
    covered_need_count: int
    missing_need_count: int
    acquired_observation_count: int
    dispatch_hash: str
    read_only: bool


class OracleObservationRequestDispatcher:
    read_only = True
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def __init__(
        self,
        acquisition_engine: RoutedObservationAcquisitionEngine,
    ) -> None:
        if not isinstance(
            acquisition_engine,
            RoutedObservationAcquisitionEngine,
        ):
            raise TypeError(
                "acquisition_engine must be RoutedObservationAcquisitionEngine"
            )

        self._acquisition_engine = acquisition_engine

    def dispatch(
        self,
        *,
        request_package: OracleObservationRequestPackage,
        acquisition_plan: ObservationAcquisitionPlan,
        dispatched_at: datetime,
    ) -> OracleObservationDispatchResult:
        if not isinstance(
            request_package,
            OracleObservationRequestPackage,
        ):
            raise TypeError(
                "request_package must be OracleObservationRequestPackage"
            )

        if not isinstance(
            acquisition_plan,
            ObservationAcquisitionPlan,
        ):
            raise TypeError(
                "acquisition_plan must be ObservationAcquisitionPlan"
            )

        if (
            request_package.acquisition_plan_hash
            != acquisition_plan.plan_hash
        ):
            raise OracleObservationRequestDispatcherError(
                "request package and acquisition plan hash mismatch"
            )

        if not isinstance(dispatched_at, datetime):
            raise TypeError("dispatched_at must be datetime")

        if dispatched_at.tzinfo is None:
            raise OracleObservationRequestDispatcherError(
                "dispatched_at must be timezone-aware"
            )

        dispatched_at = dispatched_at.astimezone(
            timezone.utc
        )

        items = []

        for plan_item in acquisition_plan.items:
            if not plan_item.covered:
                body = {
                    "ordinal": plan_item.ordinal,
                    "need_id": plan_item.need_id,
                    "covered": False,
                    "adapter_ids": (),
                    "acquisition_hash": None,
                    "observation_count": 0,
                    "evidence_hash": None,
                }

                items.append(
                    DispatchedObservationNeed(
                        ordinal=plan_item.ordinal,
                        need_id=plan_item.need_id,
                        covered=False,
                        adapter_ids=(),
                        acquisition_hash=None,
                        observation_count=0,
                        evidence_hash=None,
                        dispatch_item_hash=deterministic_sha256(body),
                    )
                )
                continue

            acquisition = self._acquisition_engine.acquire(
                query_id=(
                    f"{request_package.query_id}."
                    f"need.{plan_item.ordinal}"
                ),
                request=ObservationRouteRequest(
                    domain=plan_item.domain,
                    entity_kind=plan_item.entity_kind,
                    observation_type=plan_item.observation_type,
                ),
                assembled_at=dispatched_at,
            )

            if tuple(acquisition.invoked_adapter_ids) != tuple(
                plan_item.adapter_ids
            ):
                raise OracleObservationRequestDispatcherError(
                    "acquisition invoked adapters differ from certified plan"
                )

            body = {
                "ordinal": plan_item.ordinal,
                "need_id": plan_item.need_id,
                "covered": True,
                "adapter_ids": acquisition.invoked_adapter_ids,
                "acquisition_hash": acquisition.acquisition_hash,
                "observation_count": len(acquisition.observations),
                "evidence_hash": acquisition.evidence_bundle.evidence_hash,
            }

            items.append(
                DispatchedObservationNeed(
                    ordinal=plan_item.ordinal,
                    need_id=plan_item.need_id,
                    covered=True,
                    adapter_ids=tuple(acquisition.invoked_adapter_ids),
                    acquisition_hash=acquisition.acquisition_hash,
                    observation_count=len(acquisition.observations),
                    evidence_hash=acquisition.evidence_bundle.evidence_hash,
                    dispatch_item_hash=deterministic_sha256(body),
                )
            )

        covered_need_count = sum(
            1
            for item in items
            if item.covered
        )

        missing_need_count = len(items) - covered_need_count

        acquired_observation_count = sum(
            item.observation_count
            for item in items
        )

        body = {
            "request_id": request_package.request_id,
            "request_package_hash": request_package.package_hash,
            "plan_hash": acquisition_plan.plan_hash,
            "dispatched_at": dispatched_at,
            "item_hashes": tuple(
                item.dispatch_item_hash
                for item in items
            ),
            "covered_need_count": covered_need_count,
            "missing_need_count": missing_need_count,
            "acquired_observation_count": acquired_observation_count,
            "read_only": True,
        }

        return OracleObservationDispatchResult(
            request_id=request_package.request_id,
            request_package_hash=request_package.package_hash,
            plan_hash=acquisition_plan.plan_hash,
            dispatched_at=dispatched_at,
            items=tuple(items),
            covered_need_count=covered_need_count,
            missing_need_count=missing_need_count,
            acquired_observation_count=acquired_observation_count,
            dispatch_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_oracle_observation_request_dispatcher() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-031 must remain read-only"
        )

    if any(
        (
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
            "OI-031 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_031_REVISION",
    "OracleObservationRequestDispatcherError",
    "DispatchedObservationNeed",
    "OracleObservationDispatchResult",
    "OracleObservationRequestDispatcher",
    "verify_oracle_observation_request_dispatcher",
]
