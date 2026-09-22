from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_025_oracle_explanation_query_engine import OracleExplanationQuery
from .oi_029_observation_acquisition_plan import ObservationAcquisitionPlan

BUILD_ID = "OI-030"
OI_030_REVISION = "OI_030_ORACLE_OBSERVATION_REQUEST_PACKAGE_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False
TERMINAL_MUTATION_ALLOWED = False


class OracleObservationRequestPackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleObservationRequestPackage:
    request_id: str
    query_id: str
    query_kind: str
    subject_hint: str
    profile_id: str
    acquisition_plan_hash: str
    requested_adapter_ids: tuple[str, ...]
    missing_need_ids: tuple[str, ...]
    complete_adapter_coverage: bool
    assembled_at: datetime
    package_hash: str
    read_only: bool
    predictive: bool
    terminal_mutation_allowed: bool


class OracleObservationRequestPackageBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False
    terminal_mutation_allowed = False

    def build(
        self,
        *,
        request_id: str,
        query: OracleExplanationQuery,
        acquisition_plan: ObservationAcquisitionPlan,
        assembled_at: datetime,
    ) -> OracleObservationRequestPackage:
        request_id_value = str(request_id).strip()

        if not request_id_value:
            raise OracleObservationRequestPackageError(
                "request_id must not be empty"
            )

        if not isinstance(query, OracleExplanationQuery):
            raise TypeError(
                "query must be OracleExplanationQuery"
            )

        if not isinstance(
            acquisition_plan,
            ObservationAcquisitionPlan,
        ):
            raise TypeError(
                "acquisition_plan must be ObservationAcquisitionPlan"
            )

        if query.profile_id != acquisition_plan.profile_id:
            raise OracleObservationRequestPackageError(
                "query profile and acquisition plan profile mismatch"
            )

        if query.subject_hint != acquisition_plan.subject_hint:
            raise OracleObservationRequestPackageError(
                "query subject and acquisition plan subject mismatch"
            )

        if not isinstance(assembled_at, datetime):
            raise TypeError(
                "assembled_at must be datetime"
            )

        if assembled_at.tzinfo is None:
            raise OracleObservationRequestPackageError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(
            timezone.utc
        )

        requested_adapter_ids = tuple(
            sorted(
                {
                    adapter_id
                    for item in acquisition_plan.items
                    for adapter_id in item.adapter_ids
                }
            )
        )

        missing_need_ids = tuple(
            item.need_id
            for item in acquisition_plan.items
            if not item.covered
        )

        body = {
            "request_id": request_id_value,
            "query_id": query.query_id,
            "query_kind": query.query_kind,
            "subject_hint": query.subject_hint,
            "profile_id": query.profile_id,
            "acquisition_plan_hash": acquisition_plan.plan_hash,
            "requested_adapter_ids": requested_adapter_ids,
            "missing_need_ids": missing_need_ids,
            "complete_adapter_coverage": (
                acquisition_plan.complete_coverage
            ),
            "assembled_at": assembled_at,
            "read_only": True,
            "predictive": False,
            "terminal_mutation_allowed": False,
        }

        return OracleObservationRequestPackage(
            request_id=request_id_value,
            query_id=query.query_id,
            query_kind=query.query_kind,
            subject_hint=query.subject_hint,
            profile_id=query.profile_id,
            acquisition_plan_hash=(
                acquisition_plan.plan_hash
            ),
            requested_adapter_ids=(
                requested_adapter_ids
            ),
            missing_need_ids=missing_need_ids,
            complete_adapter_coverage=(
                acquisition_plan.complete_coverage
            ),
            assembled_at=assembled_at,
            package_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            terminal_mutation_allowed=False,
        )


def verify_oracle_observation_request_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-030 must remain read-only"
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
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-030 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_030_REVISION",
    "OracleObservationRequestPackageError",
    "OracleObservationRequestPackage",
    "OracleObservationRequestPackageBuilder",
    "verify_oracle_observation_request_package",
]
