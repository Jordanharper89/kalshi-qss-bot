from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_030_oracle_observation_request_package import (
    OracleObservationRequestPackage,
)
from .oi_031_oracle_observation_request_dispatcher import (
    OracleObservationDispatchResult,
)
from .oi_032_acquisition_coverage_reconciliation import (
    AcquisitionCoverageReconciliation,
)

BUILD_ID = "OI-033"
OI_033_REVISION = "OI_033_ORACLE_EVIDENCE_INTAKE_PACKAGE_V1"

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


class OracleEvidenceIntakePackageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleEvidenceIntakeItem:
    need_id: str
    adapter_ids: tuple[str, ...]
    evidence_hash: str | None
    observation_count: int
    satisfied: bool
    reason_code: str
    item_hash: str


@dataclass(frozen=True, slots=True)
class OracleEvidenceIntakePackage:
    intake_id: str
    request_id: str
    query_id: str
    query_kind: str
    subject_hint: str
    profile_id: str
    acquisition_status: str
    evidence_items: tuple[OracleEvidenceIntakeItem, ...]
    total_observation_count: int
    missing_need_ids: tuple[str, ...]
    complete_evidence_intake: bool
    assembled_at: datetime
    intake_hash: str
    read_only: bool
    predictive: bool
    terminal_mutation_allowed: bool


class OracleEvidenceIntakePackageBuilder:
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
        intake_id: str,
        request_package: OracleObservationRequestPackage,
        dispatch: OracleObservationDispatchResult,
        reconciliation: AcquisitionCoverageReconciliation,
        assembled_at: datetime,
    ) -> OracleEvidenceIntakePackage:
        intake_id_value = str(intake_id).strip()

        if not intake_id_value:
            raise OracleEvidenceIntakePackageError(
                "intake_id must not be empty"
            )

        if not isinstance(
            request_package,
            OracleObservationRequestPackage,
        ):
            raise TypeError(
                "request_package must be OracleObservationRequestPackage"
            )

        if not isinstance(
            dispatch,
            OracleObservationDispatchResult,
        ):
            raise TypeError(
                "dispatch must be OracleObservationDispatchResult"
            )

        if not isinstance(
            reconciliation,
            AcquisitionCoverageReconciliation,
        ):
            raise TypeError(
                "reconciliation must be AcquisitionCoverageReconciliation"
            )

        if (
            dispatch.request_package_hash
            != request_package.package_hash
        ):
            raise OracleEvidenceIntakePackageError(
                "dispatch does not belong to request package"
            )

        if (
            reconciliation.dispatch_hash
            != dispatch.dispatch_hash
        ):
            raise OracleEvidenceIntakePackageError(
                "reconciliation does not belong to dispatch"
            )

        if not isinstance(assembled_at, datetime):
            raise TypeError(
                "assembled_at must be datetime"
            )

        if assembled_at.tzinfo is None:
            raise OracleEvidenceIntakePackageError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(
            timezone.utc
        )

        dispatch_by_need = {
            item.need_id: item
            for item in dispatch.items
        }

        items = []

        for reconciled in reconciliation.items:
            dispatched = dispatch_by_need.get(
                reconciled.need_id
            )

            if dispatched is None:
                raise OracleEvidenceIntakePackageError(
                    f"dispatch missing reconciled need: "
                    f"{reconciled.need_id}"
                )

            body = {
                "need_id": reconciled.need_id,
                "adapter_ids": dispatched.adapter_ids,
                "evidence_hash": dispatched.evidence_hash,
                "observation_count": reconciled.observation_count,
                "satisfied": reconciled.satisfied,
                "reason_code": reconciled.reason_code,
            }

            items.append(
                OracleEvidenceIntakeItem(
                    need_id=reconciled.need_id,
                    adapter_ids=dispatched.adapter_ids,
                    evidence_hash=dispatched.evidence_hash,
                    observation_count=reconciled.observation_count,
                    satisfied=reconciled.satisfied,
                    reason_code=reconciled.reason_code,
                    item_hash=deterministic_sha256(body),
                )
            )

        missing_need_ids = tuple(
            item.need_id
            for item in items
            if not item.satisfied
        )

        complete = (
            reconciliation.unsatisfied_count == 0
            and bool(items)
        )

        body = {
            "intake_id": intake_id_value,
            "request_id": request_package.request_id,
            "query_id": request_package.query_id,
            "query_kind": request_package.query_kind,
            "subject_hint": request_package.subject_hint,
            "profile_id": request_package.profile_id,
            "acquisition_status": reconciliation.status,
            "evidence_item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "total_observation_count": (
                reconciliation.observation_count
            ),
            "missing_need_ids": missing_need_ids,
            "complete_evidence_intake": complete,
            "assembled_at": assembled_at,
            "read_only": True,
            "predictive": False,
            "terminal_mutation_allowed": False,
        }

        return OracleEvidenceIntakePackage(
            intake_id=intake_id_value,
            request_id=request_package.request_id,
            query_id=request_package.query_id,
            query_kind=request_package.query_kind,
            subject_hint=request_package.subject_hint,
            profile_id=request_package.profile_id,
            acquisition_status=reconciliation.status,
            evidence_items=tuple(items),
            total_observation_count=(
                reconciliation.observation_count
            ),
            missing_need_ids=missing_need_ids,
            complete_evidence_intake=complete,
            assembled_at=assembled_at,
            intake_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            terminal_mutation_allowed=False,
        )


def verify_oracle_evidence_intake_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-033 must remain read-only"
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
            "OI-033 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_033_REVISION",
    "OracleEvidenceIntakePackageError",
    "OracleEvidenceIntakeItem",
    "OracleEvidenceIntakePackage",
    "OracleEvidenceIntakePackageBuilder",
    "verify_oracle_evidence_intake_package",
]
