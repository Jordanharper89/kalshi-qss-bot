from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_venue_reconciliation_evidence_contract.py"
)

TEST_PATH = (
    ROOT
    / "test_int_028_qseries_venue_reconciliation_evidence_contract.py"
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
    INT-028 — Q Series Venue Reconciliation Evidence Contract.

    This module defines the canonical immutable evidence record returned by a
    future venue reconciliation boundary for an INT-027 reconciliation request.

    INT-028 defines evidence contracts only. It does not query a venue.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns execution-state and reconciliation control.
    * Venue evidence must reference a canonical INT-027 request.
    * Raw venue responses cannot flow directly into portfolio state.
    * No exchange, broker, account, or portfolio API is called.
    * No fill is confirmed by this module.
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


    SCHEMA_VERSION = "INT-028"
    ENGINE_ID = "INT-028"
    SOURCE_RECONCILIATION_SCHEMA = "INT-027"


    class VenueReconciliationEvidenceContractError(ValueError):
        """Raised when an INT-028 venue evidence contract is invalid."""


    class VenueEvidenceStatus(str, Enum):
        NOT_QUERIED = "not_queried"
        OBSERVED = "observed"
        UNAVAILABLE = "unavailable"
        FAILED = "failed"


    class VenueOrderState(str, Enum):
        UNKNOWN = "unknown"
        ABSENT = "absent"
        PENDING = "pending"
        RESTING = "resting"
        PARTIALLY_FILLED = "partially_filled"
        FILLED = "filled"
        CANCELED = "canceled"
        REJECTED = "rejected"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise VenueReconciliationEvidenceContractError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise VenueReconciliationEvidenceContractError(
                f"{field_name} must not be empty"
            )

        return normalized


    def _normalize_optional_string(
        value: Any,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        return _require_non_empty_string(
            value,
            field_name,
        )


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
            raise VenueReconciliationEvidenceContractError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise VenueReconciliationEvidenceContractError(
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
                raise VenueReconciliationEvidenceContractError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise VenueReconciliationEvidenceContractError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise VenueReconciliationEvidenceContractError(
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
            raise VenueReconciliationEvidenceContractError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise VenueReconciliationEvidenceContractError(
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
            raise VenueReconciliationEvidenceContractError(
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
            raise VenueReconciliationEvidenceContractError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class VenueReconciliationEvidence:
        """
        Immutable INT-028 venue reconciliation evidence.

        This record represents caller-supplied venue observations only.

        Even when order_state is FILLED, INT-028 does not confirm a fill for
        Q Series. A later canonical reconciliation engine must validate this
        evidence before execution state may advance.
        """

        evidence_id: str
        reconciliation_request_id: str
        reconciliation_request_hash: str
        result_id: str
        result_hash: str
        adapter_id: str
        adapter_reference: str
        venue_reference: str
        evidence_status: VenueEvidenceStatus
        order_state: VenueOrderState
        observed_at: str
        venue_updated_at: str | None
        reason_codes: tuple[str, ...]
        explanation: str
        venue_details: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        venue_query_record: bool = True
        fill_confirmed: bool = False
        funds_moved: bool = False
        portfolio_mutated: bool = False
        reconciliation_engine_required: bool = True
        evidence_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "evidence_id",
                _require_non_empty_string(
                    self.evidence_id,
                    "evidence_id",
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
                "adapter_reference",
                _require_non_empty_string(
                    self.adapter_reference,
                    "adapter_reference",
                ),
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
                self.evidence_status,
                VenueEvidenceStatus,
            ):
                object.__setattr__(
                    self,
                    "evidence_status",
                    VenueEvidenceStatus(
                        str(self.evidence_status).strip().lower()
                    ),
                )

            if not isinstance(
                self.order_state,
                VenueOrderState,
            ):
                object.__setattr__(
                    self,
                    "order_state",
                    VenueOrderState(
                        str(self.order_state).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "observed_at",
                _normalize_timestamp(
                    self.observed_at,
                    "observed_at",
                ),
            )

            if self.venue_updated_at is not None:
                object.__setattr__(
                    self,
                    "venue_updated_at",
                    _normalize_timestamp(
                        self.venue_updated_at,
                        "venue_updated_at",
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
                "venue_details",
                _freeze_mapping(
                    self.venue_details,
                    "venue_details",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise VenueReconciliationEvidenceContractError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise VenueReconciliationEvidenceContractError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise VenueReconciliationEvidenceContractError(
                    "INT-028 evidence records must be read_only"
                )

            if self.venue_query_record is not True:
                raise VenueReconciliationEvidenceContractError(
                    "INT-028 must identify a venue query record"
                )

            if self.fill_confirmed is not False:
                raise VenueReconciliationEvidenceContractError(
                    "INT-028 cannot confirm fills"
                )

            if self.funds_moved is not False:
                raise VenueReconciliationEvidenceContractError(
                    "INT-028 cannot report fund movement"
                )

            if self.portfolio_mutated is not False:
                raise VenueReconciliationEvidenceContractError(
                    "INT-028 cannot report portfolio mutation"
                )

            if self.reconciliation_engine_required is not True:
                raise VenueReconciliationEvidenceContractError(
                    "INT-028 must require a reconciliation engine"
                )

            if (
                self.evidence_status
                is VenueEvidenceStatus.OBSERVED
                and self.order_state
                is VenueOrderState.UNKNOWN
            ):
                raise VenueReconciliationEvidenceContractError(
                    "observed evidence must identify a non-unknown order state"
                )

            if (
                self.evidence_status
                in {
                    VenueEvidenceStatus.NOT_QUERIED,
                    VenueEvidenceStatus.UNAVAILABLE,
                    VenueEvidenceStatus.FAILED,
                }
                and self.order_state
                is not VenueOrderState.UNKNOWN
            ):
                raise VenueReconciliationEvidenceContractError(
                    "non-observed evidence must use unknown order state"
                )

            if (
                self.evidence_status
                is VenueEvidenceStatus.NOT_QUERIED
                and self.venue_updated_at is not None
            ):
                raise VenueReconciliationEvidenceContractError(
                    "not_queried evidence must not contain venue_updated_at"
                )

            if self.venue_updated_at is not None:
                if (
                    datetime.fromisoformat(
                        self.venue_updated_at
                    )
                    > datetime.fromisoformat(
                        self.observed_at
                    )
                ):
                    raise VenueReconciliationEvidenceContractError(
                        "venue_updated_at must not be later than observed_at"
                    )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.evidence_hash:
                supplied_hash = _require_non_empty_string(
                    self.evidence_hash,
                    "evidence_hash",
                )

                if supplied_hash != calculated_hash:
                    raise VenueReconciliationEvidenceContractError(
                        "evidence_hash does not match evidence contents"
                    )

            object.__setattr__(
                self,
                "evidence_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "evidence_id": self.evidence_id,
                "reconciliation_request_id": (
                    self.reconciliation_request_id
                ),
                "reconciliation_request_hash": (
                    self.reconciliation_request_hash
                ),
                "result_id": self.result_id,
                "result_hash": self.result_hash,
                "adapter_id": self.adapter_id,
                "adapter_reference": (
                    self.adapter_reference
                ),
                "venue_reference": (
                    self.venue_reference
                ),
                "evidence_status": (
                    self.evidence_status.value
                ),
                "order_state": self.order_state.value,
                "observed_at": self.observed_at,
                "venue_updated_at": (
                    self.venue_updated_at
                ),
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "venue_details": _mapping_to_dict(
                    self.venue_details
                ),
                "read_only": self.read_only,
                "venue_query_record": (
                    self.venue_query_record
                ),
                "fill_confirmed": self.fill_confirmed,
                "funds_moved": self.funds_moved,
                "portfolio_mutated": (
                    self.portfolio_mutated
                ),
                "reconciliation_engine_required": (
                    self.reconciliation_engine_required
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["evidence_hash"] = (
                self.evidence_hash
            )
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    def _validate_reconciliation_request(
        request: ExecutionResultReconciliationRequest,
    ) -> None:
        if not isinstance(
            request,
            ExecutionResultReconciliationRequest,
        ):
            raise VenueReconciliationEvidenceContractError(
                "request must be an "
                "ExecutionResultReconciliationRequest"
            )

        if request.schema_version != SOURCE_RECONCILIATION_SCHEMA:
            raise VenueReconciliationEvidenceContractError(
                "request.schema_version must be INT-027"
            )

        if (
            request.status
            is not ReconciliationRequestStatus.READY_FOR_RECONCILIATION
        ):
            raise VenueReconciliationEvidenceContractError(
                "request must be ready_for_reconciliation"
            )

        if request.target is not ReconciliationTarget.VENUE_SUBMISSION:
            raise VenueReconciliationEvidenceContractError(
                "request target must be venue_submission"
            )

        if request.adapter_reference is None:
            raise VenueReconciliationEvidenceContractError(
                "venue reconciliation requires adapter_reference"
            )

        if request.venue_reference is None:
            raise VenueReconciliationEvidenceContractError(
                "venue reconciliation requires venue_reference"
            )


    def build_venue_reconciliation_evidence(
        *,
        request: ExecutionResultReconciliationRequest,
        evidence_status: VenueEvidenceStatus | str,
        order_state: VenueOrderState | str,
        observed_at: str,
        venue_updated_at: str | None,
        reason_codes: tuple[str, ...],
        explanation: str,
        venue_details: Mapping[str, Any] | None = None,
    ) -> VenueReconciliationEvidence:
        """
        Build canonical venue reconciliation evidence.

        All observations are caller supplied. No venue query occurs here.
        """

        _validate_reconciliation_request(request)

        normalized_evidence_status = (
            evidence_status
            if isinstance(
                evidence_status,
                VenueEvidenceStatus,
            )
            else VenueEvidenceStatus(
                str(evidence_status).strip().lower()
            )
        )

        normalized_order_state = (
            order_state
            if isinstance(
                order_state,
                VenueOrderState,
            )
            else VenueOrderState(
                str(order_state).strip().lower()
            )
        )

        normalized_observed_at = _normalize_timestamp(
            observed_at,
            "observed_at",
        )

        normalized_venue_updated_at = (
            None
            if venue_updated_at is None
            else _normalize_timestamp(
                venue_updated_at,
                "venue_updated_at",
            )
        )

        normalized_reason_codes = (
            _normalize_reason_codes(
                reason_codes
            )
        )

        normalized_explanation = (
            _require_non_empty_string(
                explanation,
                "explanation",
            )
        )

        frozen_details = _freeze_mapping(
            venue_details,
            "venue_details",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "reconciliation_request_id": (
                request.reconciliation_request_id
            ),
            "reconciliation_request_hash": (
                request.request_hash
            ),
            "result_id": request.result_id,
            "result_hash": request.result_hash,
            "adapter_id": request.adapter_id,
            "adapter_reference": (
                request.adapter_reference
            ),
            "venue_reference": (
                request.venue_reference
            ),
            "evidence_status": (
                normalized_evidence_status.value
            ),
            "order_state": (
                normalized_order_state.value
            ),
            "observed_at": normalized_observed_at,
            "venue_updated_at": (
                normalized_venue_updated_at
            ),
            "reason_codes": list(
                normalized_reason_codes
            ),
            "explanation": normalized_explanation,
            "venue_details": _mapping_to_dict(
                frozen_details
            ),
        }

        evidence_id = (
            "int028-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return VenueReconciliationEvidence(
            evidence_id=evidence_id,
            reconciliation_request_id=(
                request.reconciliation_request_id
            ),
            reconciliation_request_hash=(
                request.request_hash
            ),
            result_id=request.result_id,
            result_hash=request.result_hash,
            adapter_id=request.adapter_id,
            adapter_reference=(
                request.adapter_reference
            ),
            venue_reference=(
                request.venue_reference
            ),
            evidence_status=(
                normalized_evidence_status
            ),
            order_state=normalized_order_state,
            observed_at=normalized_observed_at,
            venue_updated_at=(
                normalized_venue_updated_at
            ),
            reason_codes=(
                normalized_reason_codes
            ),
            explanation=normalized_explanation,
            venue_details=frozen_details,
        )


    def build_not_queried_venue_evidence(
        *,
        request: ExecutionResultReconciliationRequest,
        observed_at: str,
        reason_code: str,
        explanation: str,
        venue_details: Mapping[str, Any] | None = None,
    ) -> VenueReconciliationEvidence:
        """
        Build deterministic evidence proving no venue query was performed.
        """

        return build_venue_reconciliation_evidence(
            request=request,
            evidence_status=VenueEvidenceStatus.NOT_QUERIED,
            order_state=VenueOrderState.UNKNOWN,
            observed_at=observed_at,
            venue_updated_at=None,
            reason_codes=(
                _require_non_empty_string(
                    reason_code,
                    "reason_code",
                ).lower(),
            ),
            explanation=explanation,
            venue_details=venue_details,
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_RECONCILIATION_SCHEMA",
        "VenueReconciliationEvidenceContractError",
        "VenueEvidenceStatus",
        "VenueOrderState",
        "VenueReconciliationEvidence",
        "canonical_json",
        "canonical_hash",
        "build_venue_reconciliation_evidence",
        "build_not_queried_venue_evidence",
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
        ENGINE_ID,
        SCHEMA_VERSION,
        VenueEvidenceStatus,
        VenueOrderState,
        VenueReconciliationEvidenceContractError,
        build_not_queried_venue_evidence,
        build_venue_reconciliation_evidence,
    )


    def expect_evidence_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except VenueReconciliationEvidenceContractError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected VenueReconciliationEvidenceContractError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-028",
            "authorization_status": "authorized",
            "opportunity_id": "opportunity-028",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-11T02:00:00-05:00"
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
            market_id="KXTEST-INT028",
            action="buy",
            order_type="limit",
            quantity="2",
            limit_price="0.52",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-int028"
            ),
            created_at=(
                "2026-07-11T02:00:01-05:00"
            ),
            expires_at=(
                "2026-07-11T02:10:00-05:00"
            ),
            rationale=(
                "Build INT-028 venue evidence contract test chain."
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
                    "2026-07-11T02:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-11T02:00:00-05:00"
                ),
                registration_reason=(
                    "INT-028 test registration."
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
                "2026-07-11T02:00:02-05:00"
            ),
        )

        admission = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-11T02:00:03-05:00"
            ),
        )

        dispatch = build_runtime_adapter_dispatch(
            request=request,
            validation=validation,
            admission=admission,
            dispatched_at=(
                "2026-07-11T02:00:04-05:00"
            ),
            expires_at=(
                "2026-07-11T02:09:00-05:00"
            ),
        )

        runtime_invocation = (
            build_runtime_adapter_invocation(
                dispatch=dispatch,
                prepared_at=(
                    "2026-07-11T02:00:05-05:00"
                ),
                expires_at=(
                    "2026-07-11T02:08:00-05:00"
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
                "2026-07-11T02:00:06-05:00"
            ),
        )

        invocation_gate = (
            evaluate_runtime_adapter_invocation_gate(
                invocation=runtime_invocation,
                dry_run_response=dry_run_response,
                evaluated_at=(
                    "2026-07-11T02:00:07-05:00"
                ),
            )
        )

        execution_invocation = (
            build_execution_adapter_invocation(
                runtime_invocation=runtime_invocation,
                gate_decision=invocation_gate,
                prepared_at=(
                    "2026-07-11T02:00:08-05:00"
                ),
                expires_at=(
                    "2026-07-11T02:07:00-05:00"
                ),
            )
        )

        safety_decision = evaluate_execution_adapter_safety(
            invocation=execution_invocation,
            evaluated_at=(
                "2026-07-11T02:00:09-05:00"
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
                "2026-07-11T02:00:10-05:00"
            ),
            adapter_reference="adapter-ref-028",
            venue_reference="venue-ref-028",
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
                    "2026-07-11T02:00:11-05:00"
                ),
            )
        )

        return (
            build_execution_result_reconciliation_request(
                validation=result_validation,
                result=result,
                requested_at=(
                    "2026-07-11T02:00:12-05:00"
                ),
                reconciliation_context={
                    "environment": "test",
                    "venue_query_performed": False,
                    "fill_confirmed": False,
                },
            )
        )


    def test_observed_evidence_contract() -> None:
        request = make_reconciliation_request()

        evidence = build_venue_reconciliation_evidence(
            request=request,
            evidence_status="observed",
            order_state="resting",
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T02:00:13-05:00"
            ),
            reason_codes=(
                "venue_order_observed",
            ),
            explanation=(
                "Caller-supplied venue evidence reports "
                "a resting order state."
            ),
            venue_details={
                "remaining_quantity": "2",
                "filled_quantity": "0",
                "venue_query_performed": True,
            },
        )

        assert evidence.schema_version == SCHEMA_VERSION
        assert evidence.engine_id == ENGINE_ID

        assert (
            evidence.evidence_status
            is VenueEvidenceStatus.OBSERVED
        )

        assert (
            evidence.order_state
            is VenueOrderState.RESTING
        )

        assert (
            evidence.reconciliation_request_id
            == request.reconciliation_request_id
        )

        assert (
            evidence.reconciliation_request_hash
            == request.request_hash
        )

        assert evidence.result_id == request.result_id
        assert evidence.result_hash == request.result_hash

        assert evidence.adapter_id == request.adapter_id

        assert (
            evidence.adapter_reference
            == request.adapter_reference
        )

        assert (
            evidence.venue_reference
            == request.venue_reference
        )

        assert evidence.read_only is True
        assert evidence.venue_query_record is True
        assert evidence.fill_confirmed is False
        assert evidence.funds_moved is False
        assert evidence.portfolio_mutated is False

        assert (
            evidence.reconciliation_engine_required
            is True
        )

        assert len(evidence.evidence_hash) == 64


    def test_filled_is_evidence_not_confirmation() -> None:
        request = make_reconciliation_request()

        evidence = build_venue_reconciliation_evidence(
            request=request,
            evidence_status="observed",
            order_state="filled",
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T02:00:13-05:00"
            ),
            reason_codes=(
                "venue_reports_filled",
            ),
            explanation=(
                "Venue evidence reports a filled state. "
                "INT-028 does not confirm the fill."
            ),
            venue_details={
                "reported_filled_quantity": "2",
                "reported_average_price": "0.52",
            },
        )

        assert (
            evidence.order_state
            is VenueOrderState.FILLED
        )

        assert evidence.fill_confirmed is False
        assert evidence.funds_moved is False
        assert evidence.portfolio_mutated is False

        assert (
            evidence.reconciliation_engine_required
            is True
        )


    def test_not_queried_evidence() -> None:
        request = make_reconciliation_request()

        evidence = build_not_queried_venue_evidence(
            request=request,
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            reason_code="venue_not_queried",
            explanation=(
                "INT-028 contract validation occurred "
                "without querying a venue."
            ),
            venue_details={
                "venue_query_performed": False,
            },
        )

        assert (
            evidence.evidence_status
            is VenueEvidenceStatus.NOT_QUERIED
        )

        assert (
            evidence.order_state
            is VenueOrderState.UNKNOWN
        )

        assert evidence.venue_updated_at is None
        assert evidence.fill_confirmed is False
        assert evidence.portfolio_mutated is False


    def test_determinism() -> None:
        request = make_reconciliation_request()

        first = build_venue_reconciliation_evidence(
            request=request,
            evidence_status="observed",
            order_state="pending",
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T02:00:13-05:00"
            ),
            reason_codes=(
                "venue_order_observed",
            ),
            explanation=(
                "Deterministic venue evidence."
            ),
            venue_details={
                "filled_quantity": "0",
                "remaining_quantity": "2",
            },
        )

        second = build_venue_reconciliation_evidence(
            request=request,
            evidence_status="observed",
            order_state="pending",
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            venue_updated_at=(
                "2026-07-11T02:00:13-05:00"
            ),
            reason_codes=(
                "venue_order_observed",
            ),
            explanation=(
                "Deterministic venue evidence."
            ),
            venue_details={
                "remaining_quantity": "2",
                "filled_quantity": "0",
            },
        )

        assert first.evidence_id == second.evidence_id

        assert (
            first.evidence_hash
            == second.evidence_hash
        )

        assert first.to_dict() == second.to_dict()

        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        request = make_reconciliation_request()

        evidence = build_not_queried_venue_evidence(
            request=request,
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            reason_code="venue_not_queried",
            explanation="Immutability evidence.",
            venue_details={
                "venue_query_performed": False,
            },
        )

        try:
            evidence.order_state = (
                VenueOrderState.FILLED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "venue evidence must be immutable"
            )

        try:
            evidence.venue_details[
                "venue_query_performed"
            ] = True
        except TypeError:
            pass
        else:
            raise AssertionError(
                "venue details must be immutable"
            )


    def test_observed_requires_known_state() -> None:
        request = make_reconciliation_request()

        expect_evidence_error(
            lambda: build_venue_reconciliation_evidence(
                request=request,
                evidence_status="observed",
                order_state="unknown",
                observed_at=(
                    "2026-07-11T02:00:14-05:00"
                ),
                venue_updated_at=(
                    "2026-07-11T02:00:13-05:00"
                ),
                reason_codes=(
                    "venue_order_observed",
                ),
                explanation=(
                    "Invalid observed evidence."
                ),
            ),
            "must identify a non-unknown order state",
        )


    def test_non_observed_requires_unknown_state() -> None:
        request = make_reconciliation_request()

        expect_evidence_error(
            lambda: build_venue_reconciliation_evidence(
                request=request,
                evidence_status="failed",
                order_state="resting",
                observed_at=(
                    "2026-07-11T02:00:14-05:00"
                ),
                venue_updated_at=None,
                reason_codes=(
                    "venue_query_failed",
                ),
                explanation=(
                    "Invalid failed evidence."
                ),
            ),
            "non-observed evidence must use unknown order state",
        )


    def test_venue_update_cannot_follow_observation() -> None:
        request = make_reconciliation_request()

        expect_evidence_error(
            lambda: build_venue_reconciliation_evidence(
                request=request,
                evidence_status="observed",
                order_state="resting",
                observed_at=(
                    "2026-07-11T02:00:14-05:00"
                ),
                venue_updated_at=(
                    "2026-07-11T02:00:15-05:00"
                ),
                reason_codes=(
                    "venue_order_observed",
                ),
                explanation=(
                    "Invalid temporal evidence."
                ),
            ),
            "must not be later than observed_at",
        )


    def test_timestamp_required() -> None:
        request = make_reconciliation_request()

        expect_evidence_error(
            lambda: build_not_queried_venue_evidence(
                request=request,
                observed_at=(
                    "2026-07-11T02:00:14"
                ),
                reason_code="venue_not_queried",
                explanation=(
                    "Timestamp validation evidence."
                ),
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_observed_evidence_contract()
        test_filled_is_evidence_not_confirmation()
        test_not_queried_evidence()
        test_determinism()
        test_immutability()
        test_observed_requires_known_state()
        test_non_observed_requires_unknown_state()
        test_venue_update_cannot_follow_observation()
        test_timestamp_required()

        request = make_reconciliation_request()

        evidence = build_not_queried_venue_evidence(
            request=request,
            observed_at=(
                "2026-07-11T02:00:14-05:00"
            ),
            reason_code=(
                "venue_evidence_contract_only"
            ),
            explanation=(
                "Venue reconciliation evidence contract validated "
                "without querying a venue."
            ),
            venue_details={
                "environment": "test",
                "venue_query_performed": False,
                "fill_confirmed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "evidence_status": (
                evidence.evidence_status.value
            ),
            "order_state": (
                evidence.order_state.value
            ),
            "adapter_id": evidence.adapter_id,
            "reason_codes": list(
                evidence.reason_codes
            ),
            "read_only": evidence.read_only,
            "venue_query_record": (
                evidence.venue_query_record
            ),
            "fill_confirmed": (
                evidence.fill_confirmed
            ),
            "funds_moved": evidence.funds_moved,
            "portfolio_mutated": (
                evidence.portfolio_mutated
            ),
            "reconciliation_engine_required": (
                evidence.reconciliation_engine_required
            ),
        }

        print(
            "[PASS] INT-028 Q Series "
            "Venue Reconciliation Evidence Contract"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    r'''
    # INT-028 Q Series Venue Reconciliation Evidence Contract
    from .qseries_venue_reconciliation_evidence_contract import (
        VenueEvidenceStatus,
        VenueOrderState,
        VenueReconciliationEvidence,
        VenueReconciliationEvidenceContractError,
        build_not_queried_venue_evidence,
        build_venue_reconciliation_evidence,
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
        "# INT-028 Q Series "
        "Venue Reconciliation Evidence Contract"
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
    print(" INT-028 INSTALLER")
    print(" Q Series Venue Reconciliation")
    print(" Evidence Contract")
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
    print("[DONE] INT-028 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_028_qseries_venue_reconciliation_evidence_contract.py"
    )


if __name__ == "__main__":
    main()