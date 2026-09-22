from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_029_observation_acquisition_plan import ObservationAcquisitionPlan
from .oi_031_oracle_observation_request_dispatcher import (
    OracleObservationDispatchResult,
)

BUILD_ID = "OI-032"
OI_032_REVISION = "OI_032_ACQUISITION_COVERAGE_RECONCILIATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False

STATUS_COMPLETE = "complete"
STATUS_PARTIAL = "partial"
STATUS_EMPTY = "empty"


class AcquisitionCoverageReconciliationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AcquisitionCoverageItem:
    need_id: str
    planned_covered: bool
    dispatched_covered: bool
    observation_count: int
    acquisition_present: bool
    satisfied: bool
    reason_code: str
    item_hash: str


@dataclass(frozen=True, slots=True)
class AcquisitionCoverageReconciliation:
    plan_hash: str
    dispatch_hash: str
    items: tuple[AcquisitionCoverageItem, ...]
    satisfied_count: int
    unsatisfied_count: int
    observation_count: int
    status: str
    reconciliation_hash: str
    read_only: bool


class AcquisitionCoverageReconciler:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def reconcile(
        self,
        *,
        plan: ObservationAcquisitionPlan,
        dispatch: OracleObservationDispatchResult,
    ) -> AcquisitionCoverageReconciliation:
        if not isinstance(plan, ObservationAcquisitionPlan):
            raise TypeError(
                "plan must be ObservationAcquisitionPlan"
            )

        if not isinstance(
            dispatch,
            OracleObservationDispatchResult,
        ):
            raise TypeError(
                "dispatch must be OracleObservationDispatchResult"
            )

        if dispatch.plan_hash != plan.plan_hash:
            raise AcquisitionCoverageReconciliationError(
                "dispatch and plan hash mismatch"
            )

        dispatch_by_need = {
            item.need_id: item
            for item in dispatch.items
        }

        if len(dispatch_by_need) != len(dispatch.items):
            raise AcquisitionCoverageReconciliationError(
                "duplicate dispatch need_id"
            )

        items = []

        for plan_item in plan.items:
            dispatched = dispatch_by_need.get(
                plan_item.need_id
            )

            if dispatched is None:
                raise AcquisitionCoverageReconciliationError(
                    f"dispatch missing planned need: {plan_item.need_id}"
                )

            acquisition_present = (
                dispatched.acquisition_hash is not None
            )

            if not plan_item.covered:
                satisfied = False
                reason = "adapter_capability_missing"
            elif dispatched.observation_count < 1:
                satisfied = False
                reason = "no_observation_returned"
            elif not acquisition_present:
                satisfied = False
                reason = "acquisition_record_missing"
            else:
                satisfied = True
                reason = "satisfied"

            body = {
                "need_id": plan_item.need_id,
                "planned_covered": plan_item.covered,
                "dispatched_covered": dispatched.covered,
                "observation_count": dispatched.observation_count,
                "acquisition_present": acquisition_present,
                "satisfied": satisfied,
                "reason_code": reason,
            }

            items.append(
                AcquisitionCoverageItem(
                    need_id=plan_item.need_id,
                    planned_covered=plan_item.covered,
                    dispatched_covered=dispatched.covered,
                    observation_count=dispatched.observation_count,
                    acquisition_present=acquisition_present,
                    satisfied=satisfied,
                    reason_code=reason,
                    item_hash=deterministic_sha256(body),
                )
            )

        satisfied_count = sum(
            1
            for item in items
            if item.satisfied
        )

        unsatisfied_count = len(items) - satisfied_count

        observation_count = sum(
            item.observation_count
            for item in items
        )

        if not items or satisfied_count == 0:
            status = STATUS_EMPTY
        elif unsatisfied_count == 0:
            status = STATUS_COMPLETE
        else:
            status = STATUS_PARTIAL

        body = {
            "plan_hash": plan.plan_hash,
            "dispatch_hash": dispatch.dispatch_hash,
            "item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "satisfied_count": satisfied_count,
            "unsatisfied_count": unsatisfied_count,
            "observation_count": observation_count,
            "status": status,
            "read_only": True,
        }

        return AcquisitionCoverageReconciliation(
            plan_hash=plan.plan_hash,
            dispatch_hash=dispatch.dispatch_hash,
            items=tuple(items),
            satisfied_count=satisfied_count,
            unsatisfied_count=unsatisfied_count,
            observation_count=observation_count,
            status=status,
            reconciliation_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_acquisition_coverage_reconciliation() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-032 must remain read-only"
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
            "OI-032 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_032_REVISION",
    "STATUS_COMPLETE",
    "STATUS_PARTIAL",
    "STATUS_EMPTY",
    "AcquisitionCoverageReconciliationError",
    "AcquisitionCoverageItem",
    "AcquisitionCoverageReconciliation",
    "AcquisitionCoverageReconciler",
    "verify_acquisition_coverage_reconciliation",
]
