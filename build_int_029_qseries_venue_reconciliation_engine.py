from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_venue_reconciliation_engine.py"
)

TEST_PATH = (
    ROOT
    / "test_int_029_qseries_venue_reconciliation_engine.py"
)

PACKAGE_INIT_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "__init__.py"
)


MODULE_CONTENT = dedent(
    r'''
    """
    INT-029 — Q Series Venue Reconciliation Engine.

    This module evaluates canonical INT-027 reconciliation requests together
    with INT-028 venue reconciliation evidence.

    INT-029 interprets venue order-state evidence only.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns execution-state and reconciliation control.
    * Raw venue responses cannot mutate Q Series state.
    * Venue evidence must match the canonical reconciliation request.
    * A venue-reported filled state is not a Q Series fill confirmation.
    * No exchange, broker, account, or portfolio API is called.
    * No funds are moved.
    * No positions or portfolios are mutated.
    * All timestamps are caller supplied.
    * All records are deterministic, immutable, replayable, auditable,
      and explainable.
    * All hashing uses canonical JSON and never repr().
    """

    from __future__ import annotations

    from dataclasses import dataclass, field
    from datetime import datetime
    from enum import Enum
    import hashlib
    import json
    from types import MappingProxyType
    from typing import Any, Mapping

    from .qseries_execution_result_reconciliation_contract import (
        ExecutionResultReconciliationRequest,
        ReconciliationRequestStatus,
        ReconciliationTarget,
    )
    from .qseries_venue_reconciliation_evidence_contract import (
        VenueEvidenceStatus,
        VenueOrderState,
        VenueReconciliationEvidence,
    )


    SCHEMA_VERSION = "INT-029"
    ENGINE_ID = "INT-029"
    SOURCE_REQUEST_SCHEMA = "INT-027"
    SOURCE_EVIDENCE_SCHEMA = "INT-028"


    class VenueReconciliationEngineError(ValueError):
        """Raised when an INT-029 reconciliation contract is invalid."""


    class VenueReconciliationStatus(str, Enum):
        RECONCILED = "reconciled"
        PENDING = "pending"
        UNRESOLVED = "unresolved"
        BLOCKED = "blocked"


    class VenueReconciliationOutcome(str, Enum):
        NO_OBSERVATION = "no_observation"
        ORDER_ABSENT = "order_absent"
        ORDER_PENDING = "order_pending"
        ORDER_RESTING = "order_resting"
        PARTIAL_FILL_REPORTED = "partial_fill_reported"
        FULL_FILL_REPORTED = "full_fill_reported"
        ORDER_CANCELED = "order_canceled"
        ORDER_REJECTED = "order_rejected"
        VENUE_EVIDENCE_UNAVAILABLE = "venue_evidence_unavailable"
        VENUE_EVIDENCE_FAILED = "venue_evidence_failed"
        INVALID_EVIDENCE_CHAIN = "invalid_evidence_chain"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise VenueReconciliationEngineError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise VenueReconciliationEngineError(
                f"{field_name} must not be empty"
            )

        return normalized


    def _normalize_timestamp(
        value: Any,
        field_name: str,
    ) -> str:
        text = _require_non_empty_string(
            value,
            field_name,
        )

        parse_value = text

        if parse_value.endswith("Z"):
            parse_value = parse_value[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(parse_value)
        except ValueError as exc:
            raise VenueReconciliationEngineError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise VenueReconciliationEngineError(
                f"{field_name} must include a timezone offset"
            )

        return parsed.isoformat()


    def _canonicalize(value: Any) -> Any:
        if value is None or isinstance(
            value,
            (str, int, bool),
        ):
            return value

        if isinstance(value, float):
            if value != value or value in (
                float("inf"),
                float("-inf"),
            ):
                raise VenueReconciliationEngineError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise VenueReconciliationEngineError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise VenueReconciliationEngineError(
            "unsupported canonical value type: "
            f"{type(value).__name__}"
        )


    def canonical_json(value: Any) -> str:
        return json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )


    def canonical_hash(value: Any) -> str:
        return hashlib.sha256(
            canonical_json(value).encode("utf-8")
        ).hexdigest()


    def _freeze_mapping(
        value: Mapping[str, Any] | None,
        field_name: str,
    ) -> Mapping[str, Any]:
        if value is None:
            return MappingProxyType({})

        if not isinstance(value, Mapping):
            raise VenueReconciliationEngineError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise VenueReconciliationEngineError(
                f"{field_name} must resolve to a mapping"
            )

        return MappingProxyType(
            json.loads(
                canonical_json(canonical_value)
            )
        )


    def _mapping_to_dict(
        value: Mapping[str, Any],
    ) -> dict[str, Any]:
        return json.loads(
            canonical_json(value)
        )


    def _normalize_reason_codes(
        values: tuple[str, ...],
    ) -> tuple[str, ...]:
        if isinstance(values, (str, bytes)):
            raise VenueReconciliationEngineError(
                "reason_codes must be an iterable of strings"
            )

        normalized = tuple(
            sorted(
                {
                    _require_non_empty_string(
                        value,
                        "reason_codes",
                    ).lower()
                    for value in values
                }
            )
        )

        if not normalized:
            raise VenueReconciliationEngineError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class VenueReconciliationDecision:
        """
        Immutable INT-029 venue reconciliation decision.

        FULL_FILL_REPORTED and PARTIAL_FILL_REPORTED represent venue evidence
        classification only. They do not confirm Q Series fills.
        """

        reconciliation_id: str
        reconciliation_request_id: str
        reconciliation_request_hash: str
        venue_evidence_id: str
        venue_evidence_hash: str
        result_id: str
        result_hash: str
        adapter_id: str
        venue_reference: str
        status: VenueReconciliationStatus
        outcome: VenueReconciliationOutcome
        observed_order_state: VenueOrderState
        reconciled_at: str
        reason_codes: tuple[str, ...]
        explanation: str
        checks: Mapping[str, Any]
        reconciliation_details: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        execution_allowed: bool = False
        venue_state_classified: bool = True
        fill_confirmed: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        fill_confirmation_required: bool = False
        reconciliation_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "reconciliation_id",
                _require_non_empty_string(
                    self.reconciliation_id,
                    "reconciliation_id",
                ),
            )
            object.__setattr__(
                self,
                "reconciliation_request_id",
                _require_non_empty_string(
                    self.reconciliation_request_id,
                    "reconciliation_request_id",
                ),
            )
            object.__setattr__(
                self,
                "reconciliation_request_hash",
                _require_non_empty_string(
                    self.reconciliation_request_hash,
                    "reconciliation_request_hash",
                ),
            )
            object.__setattr__(
                self,
                "venue_evidence_id",
                _require_non_empty_string(
                    self.venue_evidence_id,
                    "venue_evidence_id",
                ),
            )
            object.__setattr__(
                self,
                "venue_evidence_hash",
                _require_non_empty_string(
                    self.venue_evidence_hash,
                    "venue_evidence_hash",
                ),
            )
            object.__setattr__(
                self,
                "result_id",
                _require_non_empty_string(
                    self.result_id,
                    "result_id",
                ),
            )
            object.__setattr__(
                self,
                "result_hash",
                _require_non_empty_string(
                    self.result_hash,
                    "result_hash",
                ),
            )
            object.__setattr__(
                self,
                "adapter_id",
                _require_non_empty_string(
                    self.adapter_id,
                    "adapter_id",
                ).lower(),
            )
            object.__setattr__(
                self,
                "venue_reference",
                _require_non_empty_string(
                    self.venue_reference,
                    "venue_reference",
                ),
            )

            if not isinstance(
                self.status,
                VenueReconciliationStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    VenueReconciliationStatus(
                        str(self.status).strip().lower()
                    ),
                )

            if not isinstance(
                self.outcome,
                VenueReconciliationOutcome,
            ):
                object.__setattr__(
                    self,
                    "outcome",
                    VenueReconciliationOutcome(
                        str(self.outcome).strip().lower()
                    ),
                )

            if not isinstance(
                self.observed_order_state,
                VenueOrderState,
            ):
                object.__setattr__(
                    self,
                    "observed_order_state",
                    VenueOrderState(
                        str(self.observed_order_state).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "reconciled_at",
                _normalize_timestamp(
                    self.reconciled_at,
                    "reconciled_at",
                ),
            )
            object.__setattr__(
                self,
                "reason_codes",
                _normalize_reason_codes(
                    self.reason_codes
                ),
            )
            object.__setattr__(
                self,
                "explanation",
                _require_non_empty_string(
                    self.explanation,
                    "explanation",
                ),
            )
            object.__setattr__(
                self,
                "checks",
                _freeze_mapping(
                    self.checks,
                    "checks",
                ),
            )
            object.__setattr__(
                self,
                "reconciliation_details",
                _freeze_mapping(
                    self.reconciliation_details,
                    "reconciliation_details",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise VenueReconciliationEngineError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise VenueReconciliationEngineError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise VenueReconciliationEngineError(
                    "INT-029 reconciliation decisions must be read_only"
                )

            if self.execution_allowed is not False:
                raise VenueReconciliationEngineError(
                    "INT-029 must not directly allow execution"
                )

            if self.venue_state_classified is not True:
                raise VenueReconciliationEngineError(
                    "INT-029 must identify venue-state classification"
                )

            if self.fill_confirmed is not False:
                raise VenueReconciliationEngineError(
                    "INT-029 cannot confirm fills"
                )

            if self.funds_moved is not False:
                raise VenueReconciliationEngineError(
                    "INT-029 cannot report fund movement"
                )

            if self.portfolio_mutated is not False:
                raise VenueReconciliationEngineError(
                    "INT-029 cannot report portfolio mutation"
                )

            fill_reported_outcomes = {
                VenueReconciliationOutcome.PARTIAL_FILL_REPORTED,
                VenueReconciliationOutcome.FULL_FILL_REPORTED,
            }

            if self.outcome in fill_reported_outcomes:
                if self.fill_confirmation_required is not True:
                    raise VenueReconciliationEngineError(
                        "reported fill outcomes must require fill confirmation"
                    )
            else:
                if self.fill_confirmation_required is not False:
                    raise VenueReconciliationEngineError(
                        "non-fill outcomes must not require fill confirmation"
                    )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.reconciliation_hash:
                supplied_hash = _require_non_empty_string(
                    self.reconciliation_hash,
                    "reconciliation_hash",
                )

                if supplied_hash != calculated_hash:
                    raise VenueReconciliationEngineError(
                        "reconciliation_hash does not match decision contents"
                    )

            object.__setattr__(
                self,
                "reconciliation_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "reconciliation_id": self.reconciliation_id,
                "reconciliation_request_id": (
                    self.reconciliation_request_id
                ),
                "reconciliation_request_hash": (
                    self.reconciliation_request_hash
                ),
                "venue_evidence_id": self.venue_evidence_id,
                "venue_evidence_hash": self.venue_evidence_hash,
                "result_id": self.result_id,
                "result_hash": self.result_hash,
                "adapter_id": self.adapter_id,
                "venue_reference": self.venue_reference,
                "status": self.status.value,
                "outcome": self.outcome.value,
                "observed_order_state": (
                    self.observed_order_state.value
                ),
                "reconciled_at": self.reconciled_at,
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "checks": _mapping_to_dict(
                    self.checks
                ),
                "reconciliation_details": _mapping_to_dict(
                    self.reconciliation_details
                ),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "venue_state_classified": (
                    self.venue_state_classified
                ),
                "fill_confirmed": self.fill_confirmed,
                "funds_moved": self.funds_moved,
                "portfolio_mutated": (
                    self.portfolio_mutated
                ),
                "fill_confirmation_required": (
                    self.fill_confirmation_required
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["reconciliation_hash"] = (
                self.reconciliation_hash
            )
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    def _classify_observation(
        evidence: VenueReconciliationEvidence,
    ) -> tuple[
        VenueReconciliationStatus,
        VenueReconciliationOutcome,
        tuple[str, ...],
        str,
        bool,
    ]:
        if evidence.evidence_status is VenueEvidenceStatus.NOT_QUERIED:
            return (
                VenueReconciliationStatus.UNRESOLVED,
                VenueReconciliationOutcome.NO_OBSERVATION,
                ("venue_not_queried",),
                (
                    "No venue query evidence is available. Venue state remains "
                    "unresolved and no Q Series fill is confirmed."
                ),
                False,
            )

        if evidence.evidence_status is VenueEvidenceStatus.UNAVAILABLE:
            return (
                VenueReconciliationStatus.UNRESOLVED,
                VenueReconciliationOutcome.VENUE_EVIDENCE_UNAVAILABLE,
                ("venue_evidence_unavailable",),
                (
                    "Venue evidence is unavailable. Reconciliation remains "
                    "unresolved and no Q Series fill is confirmed."
                ),
                False,
            )

        if evidence.evidence_status is VenueEvidenceStatus.FAILED:
            return (
                VenueReconciliationStatus.UNRESOLVED,
                VenueReconciliationOutcome.VENUE_EVIDENCE_FAILED,
                ("venue_evidence_failed",),
                (
                    "The venue evidence operation failed. Reconciliation "
                    "remains unresolved and no Q Series fill is confirmed."
                ),
                False,
            )

        state_mapping = {
            VenueOrderState.ABSENT: (
                VenueReconciliationStatus.RECONCILED,
                VenueReconciliationOutcome.ORDER_ABSENT,
                "venue_order_absent",
                (
                    "Venue evidence reports that the referenced order is "
                    "absent. No Q Series fill is confirmed."
                ),
                False,
            ),
            VenueOrderState.PENDING: (
                VenueReconciliationStatus.PENDING,
                VenueReconciliationOutcome.ORDER_PENDING,
                "venue_order_pending",
                (
                    "Venue evidence reports a pending order. Reconciliation "
                    "remains pending and no Q Series fill is confirmed."
                ),
                False,
            ),
            VenueOrderState.RESTING: (
                VenueReconciliationStatus.PENDING,
                VenueReconciliationOutcome.ORDER_RESTING,
                "venue_order_resting",
                (
                    "Venue evidence reports a resting order. Reconciliation "
                    "remains pending and no Q Series fill is confirmed."
                ),
                False,
            ),
            VenueOrderState.PARTIALLY_FILLED: (
                VenueReconciliationStatus.RECONCILED,
                VenueReconciliationOutcome.PARTIAL_FILL_REPORTED,
                "venue_partial_fill_reported",
                (
                    "Venue evidence reports a partial fill. INT-029 classifies "
                    "that observation only; a later fill-confirmation boundary "
                    "must validate it before Q Series execution state changes."
                ),
                True,
            ),
            VenueOrderState.FILLED: (
                VenueReconciliationStatus.RECONCILED,
                VenueReconciliationOutcome.FULL_FILL_REPORTED,
                "venue_full_fill_reported",
                (
                    "Venue evidence reports a full fill. INT-029 classifies "
                    "that observation only; a later fill-confirmation boundary "
                    "must validate it before Q Series execution state changes."
                ),
                True,
            ),
            VenueOrderState.CANCELED: (
                VenueReconciliationStatus.RECONCILED,
                VenueReconciliationOutcome.ORDER_CANCELED,
                "venue_order_canceled",
                (
                    "Venue evidence reports a canceled order. The venue state "
                    "is reconciled and no Q Series fill is confirmed."
                ),
                False,
            ),
            VenueOrderState.REJECTED: (
                VenueReconciliationStatus.RECONCILED,
                VenueReconciliationOutcome.ORDER_REJECTED,
                "venue_order_rejected",
                (
                    "Venue evidence reports a rejected order. The venue state "
                    "is reconciled and no Q Series fill is confirmed."
                ),
                False,
            ),
        }

        selected = state_mapping.get(
            evidence.order_state
        )

        if selected is None:
            return (
                VenueReconciliationStatus.UNRESOLVED,
                VenueReconciliationOutcome.NO_OBSERVATION,
                ("venue_order_state_unknown",),
                (
                    "Venue evidence does not contain a classifiable order "
                    "state. No Q Series fill is confirmed."
                ),
                False,
            )

        status, outcome, reason_code, explanation, confirmation = selected

        return (
            status,
            outcome,
            (reason_code,),
            explanation,
            confirmation,
        )


    def reconcile_venue_evidence(
        *,
        request: ExecutionResultReconciliationRequest,
        evidence: VenueReconciliationEvidence,
        reconciled_at: str,
        reconciliation_details: Mapping[str, Any] | None = None,
    ) -> VenueReconciliationDecision:
        """
        Evaluate canonical venue evidence for an INT-027 request.

        No venue query, fill confirmation, or portfolio mutation occurs.
        """

        if not isinstance(
            request,
            ExecutionResultReconciliationRequest,
        ):
            raise VenueReconciliationEngineError(
                "request must be an "
                "ExecutionResultReconciliationRequest"
            )

        if not isinstance(
            evidence,
            VenueReconciliationEvidence,
        ):
            raise VenueReconciliationEngineError(
                "evidence must be a VenueReconciliationEvidence"
            )

        if request.schema_version != SOURCE_REQUEST_SCHEMA:
            raise VenueReconciliationEngineError(
                "request.schema_version must be INT-027"
            )

        if evidence.schema_version != SOURCE_EVIDENCE_SCHEMA:
            raise VenueReconciliationEngineError(
                "evidence.schema_version must be INT-028"
            )

        normalized_reconciled_at = _normalize_timestamp(
            reconciled_at,
            "reconciled_at",
        )

        checks = {
            "request_ready": (
                request.status
                is ReconciliationRequestStatus.READY_FOR_RECONCILIATION
            ),
            "request_target_is_venue": (
                request.target
                is ReconciliationTarget.VENUE_SUBMISSION
            ),
            "request_reconciliation_required": (
                request.reconciliation_required is True
            ),
            "request_id_match": (
                request.reconciliation_request_id
                == evidence.reconciliation_request_id
            ),
            "request_hash_match": (
                request.request_hash
                == evidence.reconciliation_request_hash
            ),
            "result_id_match": (
                request.result_id
                == evidence.result_id
            ),
            "result_hash_match": (
                request.result_hash
                == evidence.result_hash
            ),
            "adapter_identity_match": (
                request.adapter_id
                == evidence.adapter_id
            ),
            "adapter_reference_match": (
                request.adapter_reference
                == evidence.adapter_reference
            ),
            "venue_reference_match": (
                request.venue_reference
                == evidence.venue_reference
            ),
            "request_read_only": (
                request.read_only is True
            ),
            "request_execution_disabled": (
                request.execution_allowed is False
            ),
            "request_fill_not_confirmed": (
                request.fill_confirmed is False
            ),
            "request_funds_not_moved": (
                request.funds_moved is False
            ),
            "request_portfolio_not_mutated": (
                request.portfolio_mutated is False
            ),
            "evidence_read_only": (
                evidence.read_only is True
            ),
            "evidence_fill_not_confirmed": (
                evidence.fill_confirmed is False
            ),
            "evidence_funds_not_moved": (
                evidence.funds_moved is False
            ),
            "evidence_portfolio_not_mutated": (
                evidence.portfolio_mutated is False
            ),
            "evidence_requires_engine": (
                evidence.reconciliation_engine_required is True
            ),
            "reconciliation_not_before_evidence": (
                datetime.fromisoformat(
                    normalized_reconciled_at
                )
                >= datetime.fromisoformat(
                    evidence.observed_at
                )
            ),
        }

        reason_mapping = {
            "request_ready": (
                "reconciliation_request_not_ready"
            ),
            "request_target_is_venue": (
                "reconciliation_target_not_venue"
            ),
            "request_reconciliation_required": (
                "reconciliation_requirement_missing"
            ),
            "request_id_match": (
                "reconciliation_request_id_mismatch"
            ),
            "request_hash_match": (
                "reconciliation_request_hash_mismatch"
            ),
            "result_id_match": (
                "result_id_mismatch"
            ),
            "result_hash_match": (
                "result_hash_mismatch"
            ),
            "adapter_identity_match": (
                "adapter_identity_mismatch"
            ),
            "adapter_reference_match": (
                "adapter_reference_mismatch"
            ),
            "venue_reference_match": (
                "venue_reference_mismatch"
            ),
            "request_read_only": (
                "reconciliation_request_not_read_only"
            ),
            "request_execution_disabled": (
                "reconciliation_execution_boundary_invalid"
            ),
            "request_fill_not_confirmed": (
                "request_fill_confirmation_detected"
            ),
            "request_funds_not_moved": (
                "request_fund_movement_detected"
            ),
            "request_portfolio_not_mutated": (
                "request_portfolio_mutation_detected"
            ),
            "evidence_read_only": (
                "venue_evidence_not_read_only"
            ),
            "evidence_fill_not_confirmed": (
                "venue_evidence_fill_confirmation_detected"
            ),
            "evidence_funds_not_moved": (
                "venue_evidence_fund_movement_detected"
            ),
            "evidence_portfolio_not_mutated": (
                "venue_evidence_portfolio_mutation_detected"
            ),
            "evidence_requires_engine": (
                "reconciliation_engine_requirement_missing"
            ),
            "reconciliation_not_before_evidence": (
                "reconciliation_precedes_evidence"
            ),
        }

        failed_reason_codes = [
            reason_mapping[check_name]
            for check_name, passed in checks.items()
            if not passed
        ]

        if failed_reason_codes:
            status = VenueReconciliationStatus.BLOCKED
            outcome = (
                VenueReconciliationOutcome.INVALID_EVIDENCE_CHAIN
            )
            reason_codes = tuple(
                failed_reason_codes
            )
            explanation = (
                "The INT-027 reconciliation request and INT-028 venue "
                "evidence failed one or more INT-029 evidence-chain checks. "
                "Venue-state advancement is blocked and no Q Series fill is "
                "confirmed."
            )
            fill_confirmation_required = False
        else:
            (
                status,
                outcome,
                reason_codes,
                explanation,
                fill_confirmation_required,
            ) = _classify_observation(
                evidence
            )

        frozen_details = _freeze_mapping(
            reconciliation_details,
            "reconciliation_details",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "reconciliation_request_id": (
                request.reconciliation_request_id
            ),
            "reconciliation_request_hash": (
                request.request_hash
            ),
            "venue_evidence_id": (
                evidence.evidence_id
            ),
            "venue_evidence_hash": (
                evidence.evidence_hash
            ),
            "result_id": request.result_id,
            "result_hash": request.result_hash,
            "adapter_id": request.adapter_id,
            "venue_reference": (
                request.venue_reference
            ),
            "status": status.value,
            "outcome": outcome.value,
            "observed_order_state": (
                evidence.order_state.value
            ),
            "reconciled_at": normalized_reconciled_at,
            "reason_codes": sorted(
                set(reason_codes)
            ),
            "checks": checks,
            "reconciliation_details": _mapping_to_dict(
                frozen_details
            ),
            "fill_confirmation_required": (
                fill_confirmation_required
            ),
        }

        reconciliation_id = (
            "int029-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return VenueReconciliationDecision(
            reconciliation_id=reconciliation_id,
            reconciliation_request_id=(
                request.reconciliation_request_id
            ),
            reconciliation_request_hash=(
                request.request_hash
            ),
            venue_evidence_id=(
                evidence.evidence_id
            ),
            venue_evidence_hash=(
                evidence.evidence_hash
            ),
            result_id=request.result_id,
            result_hash=request.result_hash,
            adapter_id=request.adapter_id,
            venue_reference=(
                request.venue_reference
            ),
            status=status,
            outcome=outcome,
            observed_order_state=(
                evidence.order_state
            ),
            reconciled_at=normalized_reconciled_at,
            reason_codes=reason_codes,
            explanation=explanation,
            checks=checks,
            reconciliation_details=frozen_details,
            fill_confirmation_required=(
                fill_confirmation_required
            ),
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_REQUEST_SCHEMA",
        "SOURCE_EVIDENCE_SCHEMA",
        "VenueReconciliationEngineError",
        "VenueReconciliationStatus",
        "VenueReconciliationOutcome",
        "VenueReconciliationDecision",
        "canonical_json",
        "canonical_hash",
        "reconcile_venue_evidence",
    ]
    '''
).lstrip()


TEST_CONTENT = dedent(
    r'''
    from __future__ import annotations

    from dataclasses import FrozenInstanceError

    from qseries_v2.integration.qseries_dry_run_runtime_adapter import (
        QSeriesDryRunRuntimeAdapter,
    )
    from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
        evaluate_execution_adapter_admission,
    )
    from qseries_v2.integration.qseries_execution_adapter_contract import (
        build_execution_adapter_request,
    )
    from qseries_v2.integration.qseries_execution_adapter_invocation_contract import (
        build_execution_adapter_invocation,
    )
    from qseries_v2.integration.qseries_execution_adapter_registry import (
        ExecutionAdapterRegistry,
        build_execution_adapter_registration,
        validate_execution_adapter_request,
    )
    from qseries_v2.integration.qseries_execution_adapter_result_contract import (
        build_execution_adapter_result,
    )
    from qseries_v2.integration.qseries_execution_adapter_result_validation_gate import (
        validate_execution_adapter_result,
    )
    from qseries_v2.integration.qseries_execution_adapter_safety_gate import (
        evaluate_execution_adapter_safety,
    )
    from qseries_v2.integration.qseries_execution_result_reconciliation_contract import (
        build_execution_result_reconciliation_request,
    )
    from qseries_v2.integration.qseries_runtime_adapter_dispatch_contract import (
        build_runtime_adapter_dispatch,
    )
    from qseries_v2.integration.qseries_runtime_adapter_interface import (
        build_runtime_adapter_invocation,
    )
    from qseries_v2.integration.qseries_runtime_adapter_invocation_gate import (
        evaluate_runtime_adapter_invocation_gate,
    )
    from qseries_v2.integration.qseries_venue_reconciliation_evidence_contract import (
        VenueOrderState,
        build_not_queried_venue_evidence,
        build_venue_reconciliation_evidence,
    )
    from qseries_v2.integration.qseries_venue_reconciliation_engine import (
        ENGINE_ID,
        SCHEMA_VERSION,
        VenueReconciliationEngineError,
        VenueReconciliationOutcome,
        VenueReconciliationStatus,
        reconcile_venue_evidence,
    )


    def expect_engine_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except VenueReconciliationEngineError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected VenueReconciliationEngineError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-029",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-029",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-11T03:00:00-05:00"
            ),
        }


    def make_reconciliation_request():
        request = build_execution_adapter_request(
            authorization_record=(
                make_authorization_record()
            ),
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            account_reference=(
                "account-test"
            ),
            market_id="KXTEST-INT029",
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.53",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-int029"
            ),
            created_at=(
                "2026-07-11T03:00:01-05:00"
            ),
            expires_at=(
                "2026-07-11T03:10:00-05:00"
            ),
            rationale=(
                "Build INT-029 venue reconciliation engine test chain."
            ),
        )

        registration = (
            build_execution_adapter_registration(
                adapter_id=(
                    "adapter.kalshi.execution"
                ),
                adapter_name=(
                    "Kalshi Execution Adapter"
                ),
                adapter_version="1.0.0",
                venue_id="kalshi",
                supported_market_prefixes=[
                    "kxtest",
                ],
                supported_actions=[
                    "buy",
                    "sell",
                ],
                supported_order_types=[
                    "limit",
                    "market",
                ],
                supported_price_units=[
                    "usd_probability",
                ],
                lifecycle_status="registered",
                registered_at=(
                    "2026-07-11T03:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-11T03:00:00-05:00"
                ),
                registration_reason=(
                    "INT-029 test registration."
                ),
            )
        )

        registry = ExecutionAdapterRegistry(
            [registration]
        )

        validation = validate_execution_adapter_request(
            request=request,
            registry=registry,
            validated_at=(
                "2026-07-11T03:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-11T03:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-11T03:00:04-05:00"
            ),
            expires_at=(
                "2026-07-11T03:09:00-05:00"
            ),
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-11T03:00:05-05:00"
                ),
                expires_at=(
                    "2026-07-11T03:08:00-05:00"
                ),
            )
        )

        dry_run_adapter = QSeriesDryRunRuntimeAdapter(
            adapter_id=(
                "adapter.kalshi.execution"
            ),
            adapter_version="1.0.0-dry-run",
        )

        dry_run_response = dry_run_adapter.simulate(
            invocation=runtime_invocation,
            simulated_at=(
                "2026-07-11T03:00:06-05:00"
            ),
        )

        invocation_gate = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-11T03:00:07-05:00"
                ),
            )
        )

        execution_invocation = (
            build_execution_adapter_invocation(
                runtime_invocation=runtime_invocation,
                gate_decision=invocation_gate,
                prepared_at=(
                    "2026-07-11T03:00:08-05:00"
                ),
                expires_at=(
                    "2026-07-11T03:07:00-05:00"
                ),
            )
        )

        safety_decision = evaluate_execution_adapter_safety(
            invocation=execution_invocation,
            evaluated_at=(
                "2026-07-11T03:00:09-05:00"
            ),
            safety_evidence={
                "environment": "test",
                "network_access_enabled": False,
                "execution_adapter_called": False,
                "exchange_called": False,
                "live_order_submitted": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        result = build_execution_adapter_result(
            invocation=execution_invocation,
            status="submission_accepted",
            completed_at=(
                "2026-07-11T03:00:10-05:00"
            ),
            adapter_reference="adapter-ref-029",
            venue_reference="venue-ref-029",
            reason_codes=(
                "venue_submission_accepted",
            ),
            explanation=(
                "Caller-supplied adapter evidence reports "
                "submission acceptance only."
            ),
            adapter_details={
                "fill_confirmed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        result_validation = (
            validate_execution_adapter_result(
                invocation=execution_invocation,
                safety_decision=safety_decision,
                result=result,
                validated_at=(
                    "2026-07-11T03:00:11-05:00"
                ),
            )
        )

        return (
            build_execution_result_reconciliation_request(
                validation=result_validation,
                result=result,
                requested_at=(
                    "2026-07-11T03:00:12-05:00"
                ),
                reconciliation_context={
                    "environment": "test",
                    "venue_query_performed": False,
                    "fill_confirmed": False,
                },
            )
        )


    def make_observed_evidence(
        request,
        *,
        order_state: str,
        venue_details: dict | None = None,
    ):
        return build_venue_reconciliation_evidence(
            request=request,
            evidence_status="observed",
            order_state=order_state,
            observed_at=(
                "2026-07-11T03:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T03:00:13-05:00"
            ),
            reason_codes=(
                "venue_order_observed",
            ),
            explanation=(
                f"Caller-supplied venue evidence reports "
                f"{order_state}."
            ),
            venue_details=venue_details,
        )


    def test_resting_order_pending() -> None:
        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="resting",
            venue_details={
                "remaining_quantity": "2",
                "filled_quantity": "0",
            },
        )

        decision = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
            reconciliation_details={
                "environment": "test",
                "fill_confirmation_performed": False,
            },
        )

        assert decision.schema_version == SCHEMA_VERSION
        assert decision.engine_id == ENGINE_ID

        assert (
            decision.status
            is VenueReconciliationStatus.PENDING
        )

        assert (
            decision.outcome
            is VenueReconciliationOutcome.ORDER_RESTING
        )

        assert (
            decision.observed_order_state
            is VenueOrderState.RESTING
        )

        assert decision.reason_codes == (
            "venue_order_resting",
        )

        assert (
            decision.reconciliation_request_id
            == request.reconciliation_request_id
        )

        assert (
            decision.reconciliation_request_hash
            == request.request_hash
        )

        assert (
            decision.venue_evidence_id
            == evidence.evidence_id
        )

        assert (
            decision.venue_evidence_hash
            == evidence.evidence_hash
        )

        assert decision.read_only is True
        assert decision.execution_allowed is False
        assert decision.venue_state_classified is True
        assert decision.fill_confirmed is False
        assert decision.funds_moved is False
        assert decision.portfolio_mutated is False

        assert (
            decision.fill_confirmation_required
            is False
        )

        assert len(decision.reconciliation_hash) == 64


    def test_full_fill_requires_confirmation() -> None:
        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="filled",
            venue_details={
                "reported_filled_quantity": "2",
                "reported_average_price": "0.53",
            },
        )

        decision = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
        )

        assert (
            decision.status
            is VenueReconciliationStatus.RECONCILED
        )

        assert (
            decision.outcome
            is VenueReconciliationOutcome.FULL_FILL_REPORTED
        )

        assert (
            decision.observed_order_state
            is VenueOrderState.FILLED
        )

        assert decision.reason_codes == (
            "venue_full_fill_reported",
        )

        assert decision.fill_confirmed is False

        assert (
            decision.fill_confirmation_required
            is True
        )

        assert decision.funds_moved is False
        assert decision.portfolio_mutated is False


    def test_partial_fill_requires_confirmation() -> None:
        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="partially_filled",
            venue_details={
                "reported_filled_quantity": "1",
                "reported_remaining_quantity": "1",
            },
        )

        decision = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
        )

        assert (
            decision.outcome
            is VenueReconciliationOutcome.PARTIAL_FILL_REPORTED
        )

        assert decision.fill_confirmed is False

        assert (
            decision.fill_confirmation_required
            is True
        )


    def test_not_queried_unresolved() -> None:
        request = make_reconciliation_request()

        evidence = build_not_queried_venue_evidence(
            request=request,
            observed_at=(
                "2026-07-11T03:00:14-05:00"
            ),
            reason_code="venue_not_queried",
            explanation=(
                "Venue was not queried."
            ),
        )

        decision = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
        )

        assert (
            decision.status
            is VenueReconciliationStatus.UNRESOLVED
        )

        assert (
            decision.outcome
            is VenueReconciliationOutcome.NO_OBSERVATION
        )

        assert decision.fill_confirmed is False

        assert (
            decision.fill_confirmation_required
            is False
        )


    def test_canceled_order_reconciled() -> None:
        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="canceled",
        )

        decision = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
        )

        assert (
            decision.status
            is VenueReconciliationStatus.RECONCILED
        )

        assert (
            decision.outcome
            is VenueReconciliationOutcome.ORDER_CANCELED
        )

        assert decision.fill_confirmed is False

        assert (
            decision.fill_confirmation_required
            is False
        )


    def test_determinism() -> None:
        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="filled",
            venue_details={
                "reported_average_price": "0.53",
                "reported_filled_quantity": "2",
            },
        )

        first = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
            reconciliation_details={
                "fill_confirmation_performed": False,
                "environment": "test",
            },
        )

        second = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
            reconciliation_details={
                "environment": "test",
                "fill_confirmation_performed": False,
            },
        )

        assert (
            first.reconciliation_id
            == second.reconciliation_id
        )

        assert (
            first.reconciliation_hash
            == second.reconciliation_hash
        )

        assert first.to_dict() == second.to_dict()

        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="resting",
        )

        decision = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
        )

        try:
            decision.status = (
                VenueReconciliationStatus.RECONCILED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "venue reconciliation decision must be immutable"
            )

        try:
            decision.checks[
                "request_id_match"
            ] = False
        except TypeError:
            pass
        else:
            raise AssertionError(
                "venue reconciliation checks must be immutable"
            )


    def test_reconciliation_precedes_evidence_blocked() -> None:
        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="resting",
        )

        decision = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:13-05:00"
            ),
        )

        assert (
            decision.status
            is VenueReconciliationStatus.BLOCKED
        )

        assert (
            decision.outcome
            is VenueReconciliationOutcome.INVALID_EVIDENCE_CHAIN
        )

        assert (
            "reconciliation_precedes_evidence"
            in decision.reason_codes
        )

        assert decision.fill_confirmed is False
        assert decision.portfolio_mutated is False


    def test_timestamp_required() -> None:
        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="resting",
        )

        expect_engine_error(
            lambda: reconcile_venue_evidence(
                request=request,
                evidence=evidence,
                reconciled_at=(
                    "2026-07-11T03:00:15"
                ),
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_resting_order_pending()
        test_full_fill_requires_confirmation()
        test_partial_fill_requires_confirmation()
        test_not_queried_unresolved()
        test_canceled_order_reconciled()
        test_determinism()
        test_immutability()
        test_reconciliation_precedes_evidence_blocked()
        test_timestamp_required()

        request = make_reconciliation_request()

        evidence = make_observed_evidence(
            request,
            order_state="filled",
            venue_details={
                "reported_filled_quantity": "2",
                "reported_average_price": "0.53",
            },
        )

        decision = reconcile_venue_evidence(
            request=request,
            evidence=evidence,
            reconciled_at=(
                "2026-07-11T03:00:15-05:00"
            ),
            reconciliation_details={
                "environment": "test",
                "fill_confirmation_performed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "reconciliation_status": (
                decision.status.value
            ),
            "outcome": decision.outcome.value,
            "observed_order_state": (
                decision.observed_order_state.value
            ),
            "adapter_id": decision.adapter_id,
            "reason_codes": list(
                decision.reason_codes
            ),
            "read_only": decision.read_only,
            "execution_allowed": (
                decision.execution_allowed
            ),
            "venue_state_classified": (
                decision.venue_state_classified
            ),
            "fill_confirmed": (
                decision.fill_confirmed
            ),
            "fill_confirmation_required": (
                decision.fill_confirmation_required
            ),
            "funds_moved": decision.funds_moved,
            "portfolio_mutated": (
                decision.portfolio_mutated
            ),
        }

        print(
            "[PASS] INT-029 Q Series "
            "Venue Reconciliation Engine"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-029 Q Series Venue Reconciliation Engine
    from .qseries_venue_reconciliation_engine import (
        VenueReconciliationDecision,
        VenueReconciliationEngineError,
        VenueReconciliationOutcome,
        VenueReconciliationStatus,
        reconcile_venue_evidence,
    )
    '''
).strip()


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(f"[OK] Wrote {path}")


def update_package_exports(
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing = (
        path.read_text(
            encoding="utf-8"
        )
        if path.exists()
        else ""
    )

    marker = (
        "# INT-029 Q Series "
        "Venue Reconciliation Engine"
    )

    if marker in existing:
        print(
            f"[OK] Export already present in {path}"
        )
        return

    updated = existing.rstrip()

    if updated:
        updated += "\n\n"

    updated += EXPORT_BLOCK + "\n"

    path.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    print(f"[OK] Updated {path}")


def main() -> None:
    print("========================================")
    print(" INT-029 INSTALLER")
    print(" Q Series Venue Reconciliation Engine")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )
    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )
    update_package_exports(
        PACKAGE_INIT_PATH
    )

    print()
    print("[DONE] INT-029 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_029_qseries_venue_reconciliation_engine.py"
    )


if __name__ == "__main__":
    main()