from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_execution_adapter_admission_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_int_018_qseries_execution_adapter_admission_gate.py"
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
    INT-018 — Q Series Execution Adapter Admission Gate.

    This module combines an INT-016 execution-adapter request with an INT-017
    adapter-registry validation and produces the canonical admission decision
    required before a future runtime adapter may process the request.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series owns authorization and execution admission.
    * No live order is placed.
    * No exchange, broker, or account API is called.
    * No funds, positions, or portfolios are mutated.
    * All records are immutable.
    * All outputs are deterministic, replayable, auditable, and explainable.
    * All timestamps are caller supplied.
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

    from .qseries_execution_adapter_contract import (
        ExecutionAdapterRequest,
    )
    from .qseries_execution_adapter_registry import (
        AdapterValidationStatus,
        ExecutionAdapterValidation,
    )


    SCHEMA_VERSION = "INT-018"
    ENGINE_ID = "INT-018"
    SOURCE_REQUEST_SCHEMA = "INT-016"
    SOURCE_VALIDATION_SCHEMA = "INT-017"


    class ExecutionAdapterAdmissionError(ValueError):
        """Raised when an INT-018 admission contract is invalid."""


    class AdapterAdmissionStatus(str, Enum):
        ADMITTED = "admitted"
        BLOCKED = "blocked"


    def _require_non_empty_string(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise ExecutionAdapterAdmissionError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ExecutionAdapterAdmissionError(
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
            raise ExecutionAdapterAdmissionError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ExecutionAdapterAdmissionError(
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
                raise ExecutionAdapterAdmissionError(
                    "non-finite floats are not canonical"
                )

            return format(value, ".15g")

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise ExecutionAdapterAdmissionError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [
                _canonicalize(item)
                for item in value
            ]

        raise ExecutionAdapterAdmissionError(
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
            raise ExecutionAdapterAdmissionError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise ExecutionAdapterAdmissionError(
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
            raise ExecutionAdapterAdmissionError(
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
            raise ExecutionAdapterAdmissionError(
                "reason_codes must contain at least one value"
            )

        return normalized


    @dataclass(frozen=True, slots=True)
    class ExecutionAdapterAdmission:
        """
        Immutable admission record for a validated INT-016 request.

        ADMITTED means the request passed the Q Series adapter-boundary
        checks. It does not mean execution occurred and does not authorize
        bypassing a future runtime adapter safety layer.
        """

        admission_id: str
        request_id: str
        request_contract_hash: str
        validation_id: str
        validation_hash: str
        adapter_id: str
        status: AdapterAdmissionStatus
        admitted_at: str
        reason_codes: tuple[str, ...]
        explanation: str
        checks: Mapping[str, Any]
        evidence: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        execution_allowed: bool = False
        runtime_adapter_required: bool = True
        admission_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "admission_id",
                _require_non_empty_string(
                    self.admission_id,
                    "admission_id",
                ),
            )
            object.__setattr__(
                self,
                "request_id",
                _require_non_empty_string(
                    self.request_id,
                    "request_id",
                ),
            )
            object.__setattr__(
                self,
                "request_contract_hash",
                _require_non_empty_string(
                    self.request_contract_hash,
                    "request_contract_hash",
                ),
            )
            object.__setattr__(
                self,
                "validation_id",
                _require_non_empty_string(
                    self.validation_id,
                    "validation_id",
                ),
            )
            object.__setattr__(
                self,
                "validation_hash",
                _require_non_empty_string(
                    self.validation_hash,
                    "validation_hash",
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

            if not isinstance(
                self.status,
                AdapterAdmissionStatus,
            ):
                object.__setattr__(
                    self,
                    "status",
                    AdapterAdmissionStatus(
                        str(self.status).strip().lower()
                    ),
                )

            object.__setattr__(
                self,
                "admitted_at",
                _normalize_timestamp(
                    self.admitted_at,
                    "admitted_at",
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
                "evidence",
                _freeze_mapping(
                    self.evidence,
                    "evidence",
                ),
            )

            if self.schema_version != SCHEMA_VERSION:
                raise ExecutionAdapterAdmissionError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise ExecutionAdapterAdmissionError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise ExecutionAdapterAdmissionError(
                    "INT-018 admissions must be read_only"
                )

            if self.execution_allowed is not False:
                raise ExecutionAdapterAdmissionError(
                    "INT-018 must not directly allow execution"
                )

            if self.runtime_adapter_required is not True:
                raise ExecutionAdapterAdmissionError(
                    "INT-018 must require a runtime adapter"
                )

            calculated_hash = canonical_hash(
                self._hash_payload()
            )

            if self.admission_hash:
                supplied_hash = _require_non_empty_string(
                    self.admission_hash,
                    "admission_hash",
                )

                if supplied_hash != calculated_hash:
                    raise ExecutionAdapterAdmissionError(
                        "admission_hash does not match "
                        "admission contents"
                    )

            object.__setattr__(
                self,
                "admission_hash",
                calculated_hash,
            )

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "admission_id": self.admission_id,
                "request_id": self.request_id,
                "request_contract_hash": (
                    self.request_contract_hash
                ),
                "validation_id": self.validation_id,
                "validation_hash": self.validation_hash,
                "adapter_id": self.adapter_id,
                "status": self.status.value,
                "admitted_at": self.admitted_at,
                "reason_codes": list(
                    self.reason_codes
                ),
                "explanation": self.explanation,
                "checks": _mapping_to_dict(
                    self.checks
                ),
                "evidence": _mapping_to_dict(
                    self.evidence
                ),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "runtime_adapter_required": (
                    self.runtime_adapter_required
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["admission_hash"] = (
                self.admission_hash
            )
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(
                self.to_dict()
            )


    def evaluate_execution_adapter_admission(
        *,
        request: ExecutionAdapterRequest,
        validation: ExecutionAdapterValidation,
        admitted_at: str,
        evidence: Mapping[str, Any] | None = None,
    ) -> ExecutionAdapterAdmission:
        """
        Evaluate whether an INT-016 request may cross the INT-018 admission
        boundary toward a later runtime adapter.

        This function performs contract verification only. It does not call
        an adapter and does not place or submit an order.
        """

        if not isinstance(
            request,
            ExecutionAdapterRequest,
        ):
            raise ExecutionAdapterAdmissionError(
                "request must be an "
                "ExecutionAdapterRequest"
            )

        if not isinstance(
            validation,
            ExecutionAdapterValidation,
        ):
            raise ExecutionAdapterAdmissionError(
                "validation must be an "
                "ExecutionAdapterValidation"
            )

        if request.schema_version != SOURCE_REQUEST_SCHEMA:
            raise ExecutionAdapterAdmissionError(
                "request.schema_version must be INT-016"
            )

        if (
            validation.schema_version
            != SOURCE_VALIDATION_SCHEMA
        ):
            raise ExecutionAdapterAdmissionError(
                "validation.schema_version must be INT-017"
            )

        normalized_admitted_at = _normalize_timestamp(
            admitted_at,
            "admitted_at",
        )

        checks = {
            "request_id_matches": (
                validation.request_id
                == request.request_id
            ),
            "adapter_id_matches": (
                validation.adapter_id
                == request.adapter_id.lower()
            ),
            "validation_approved": (
                validation.status
                is AdapterValidationStatus.APPROVED
            ),
            "request_read_only": (
                request.read_only is True
            ),
            "request_execution_disabled": (
                request.execution_allowed is False
            ),
            "request_requires_adapter": (
                request.requires_concrete_adapter
                is True
            ),
            "validation_read_only": (
                validation.read_only is True
            ),
            "validation_execution_disabled": (
                validation.execution_allowed
                is False
            ),
            "validation_requires_runtime": (
                validation.runtime_processing_required
                is True
            ),
            "request_hash_present": bool(
                request.contract_hash
            ),
            "validation_hash_present": bool(
                validation.validation_hash
            ),
        }

        reason_codes: list[str] = []

        if not checks["request_id_matches"]:
            reason_codes.append(
                "request_id_mismatch"
            )

        if not checks["adapter_id_matches"]:
            reason_codes.append(
                "adapter_id_mismatch"
            )

        if not checks["validation_approved"]:
            reason_codes.append(
                "registry_validation_not_approved"
            )

        if not checks["request_read_only"]:
            reason_codes.append(
                "request_not_read_only"
            )

        if not checks["request_execution_disabled"]:
            reason_codes.append(
                "request_execution_boundary_invalid"
            )

        if not checks["request_requires_adapter"]:
            reason_codes.append(
                "request_adapter_requirement_missing"
            )

        if not checks["validation_read_only"]:
            reason_codes.append(
                "validation_not_read_only"
            )

        if not checks[
            "validation_execution_disabled"
        ]:
            reason_codes.append(
                "validation_execution_boundary_invalid"
            )

        if not checks[
            "validation_requires_runtime"
        ]:
            reason_codes.append(
                "runtime_requirement_missing"
            )

        if not checks["request_hash_present"]:
            reason_codes.append(
                "request_hash_missing"
            )

        if not checks["validation_hash_present"]:
            reason_codes.append(
                "validation_hash_missing"
            )

        if all(checks.values()):
            status = AdapterAdmissionStatus.ADMITTED
            reason_codes = [
                "adapter_request_admitted"
            ]
            explanation = (
                "The INT-016 request and INT-017 registry validation "
                "match, all execution-boundary invariants remain intact, "
                "and the request is admitted for later runtime-adapter "
                "processing. No execution occurred."
            )
        else:
            status = AdapterAdmissionStatus.BLOCKED
            explanation = (
                "The adapter request failed one or more INT-018 "
                "admission checks and is blocked from runtime-adapter "
                "processing. No execution occurred."
            )

        frozen_evidence = _freeze_mapping(
            evidence,
            "evidence",
        )

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "request_id": request.request_id,
            "request_contract_hash": (
                request.contract_hash
            ),
            "validation_id": (
                validation.validation_id
            ),
            "validation_hash": (
                validation.validation_hash
            ),
            "adapter_id": (
                request.adapter_id.lower()
            ),
            "status": status.value,
            "admitted_at": (
                normalized_admitted_at
            ),
            "reason_codes": sorted(
                set(reason_codes)
            ),
            "checks": checks,
            "evidence": _mapping_to_dict(
                frozen_evidence
            ),
        }

        admission_id = (
            "int018-"
            f"{canonical_hash(identity_payload)[:32]}"
        )

        return ExecutionAdapterAdmission(
            admission_id=admission_id,
            request_id=request.request_id,
            request_contract_hash=(
                request.contract_hash
            ),
            validation_id=(
                validation.validation_id
            ),
            validation_hash=(
                validation.validation_hash
            ),
            adapter_id=request.adapter_id,
            status=status,
            admitted_at=normalized_admitted_at,
            reason_codes=tuple(reason_codes),
            explanation=explanation,
            checks=checks,
            evidence=frozen_evidence,
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_REQUEST_SCHEMA",
        "SOURCE_VALIDATION_SCHEMA",
        "ExecutionAdapterAdmissionError",
        "AdapterAdmissionStatus",
        "ExecutionAdapterAdmission",
        "canonical_json",
        "canonical_hash",
        "evaluate_execution_adapter_admission",
    ]
    '''
).lstrip()


TEST_CONTENT = dedent(
    r'''
    from __future__ import annotations

    from dataclasses import FrozenInstanceError

    from qseries_v2.integration.qseries_execution_adapter_admission_gate import (
        AdapterAdmissionStatus,
        ENGINE_ID,
        SCHEMA_VERSION,
        ExecutionAdapterAdmissionError,
        evaluate_execution_adapter_admission,
    )
    from qseries_v2.integration.qseries_execution_adapter_contract import (
        build_execution_adapter_request,
    )
    from qseries_v2.integration.qseries_execution_adapter_registry import (
        ExecutionAdapterRegistry,
        build_execution_adapter_registration,
        validate_execution_adapter_request,
    )


    def expect_admission_error(
        callable_object,
        expected_text: str,
    ) -> None:
        try:
            callable_object()
        except ExecutionAdapterAdmissionError as exc:
            assert expected_text in str(exc), (
                f"expected error containing "
                f"{expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                "expected "
                "ExecutionAdapterAdmissionError "
                f"containing {expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": (
                "final-auth-0001"
            ),
            "authorization_status": (
                "authorized"
            ),
            "opportunity_id": "opp-001",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": (
                "2026-07-10T15:00:00-05:00"
            ),
        }


    def make_request(
        *,
        adapter_id: str = (
            "adapter.kalshi.execution"
        ),
        market_id: str = (
            "KXTEST-26JUL10"
        ),
    ):
        return build_execution_adapter_request(
            authorization_record=(
                make_authorization_record()
            ),
            adapter_id=adapter_id,
            account_reference=(
                "account-primary"
            ),
            market_id=market_id,
            action="buy",
            order_type="limit",
            quantity="12",
            limit_price="0.43",
            price_unit="usd_probability",
            time_in_force="gtc",
            client_order_id=(
                "client-order-001"
            ),
            created_at=(
                "2026-07-10T15:01:00-05:00"
            ),
            expires_at=(
                "2026-07-10T15:06:00-05:00"
            ),
            rationale=(
                "Authorized INT-015 adapter request."
            ),
            metadata={
                "strategy_id": (
                    "strategy.test"
                ),
            },
        )


    def make_registry():
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
                    "kxbtc",
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
                lifecycle_status=(
                    "registered"
                ),
                registered_at=(
                    "2026-07-10T15:00:00-05:00"
                ),
                effective_at=(
                    "2026-07-10T15:00:00-05:00"
                ),
                registration_reason=(
                    "Canonical test adapter "
                    "registration."
                ),
                metadata={
                    "environment": "test",
                    "live_execution_enabled": False,
                },
            )
        )

        return ExecutionAdapterRegistry(
            [registration]
        )


    def make_validation(request):
        return validate_execution_adapter_request(
            request=request,
            registry=make_registry(),
            validated_at=(
                "2026-07-10T15:01:01-05:00"
            ),
        )


    def test_admitted_contract() -> None:
        request = make_request()
        validation = make_validation(request)

        admission = (
            evaluate_execution_adapter_admission(
                request=request,
                validation=validation,
                admitted_at=(
                    "2026-07-10T15:01:02-05:00"
                ),
                evidence={
                    "runtime_adapter_connected": False,
                    "live_order_submitted": False,
                    "portfolio_mutated": False,
                },
            )
        )

        assert (
            admission.schema_version
            == SCHEMA_VERSION
        )
        assert admission.engine_id == ENGINE_ID
        assert (
            admission.status
            is AdapterAdmissionStatus.ADMITTED
        )
        assert admission.reason_codes == (
            "adapter_request_admitted",
        )
        assert (
            admission.request_id
            == request.request_id
        )
        assert (
            admission.validation_id
            == validation.validation_id
        )
        assert (
            admission.adapter_id
            == request.adapter_id
        )
        assert admission.read_only is True
        assert admission.execution_allowed is False
        assert (
            admission.runtime_adapter_required
            is True
        )
        assert len(admission.admission_hash) == 64
        assert (
            admission.checks[
                "request_id_matches"
            ]
            is True
        )
        assert (
            admission.checks[
                "adapter_id_matches"
            ]
            is True
        )
        assert (
            admission.checks[
                "validation_approved"
            ]
            is True
        )
        assert (
            admission.evidence[
                "live_order_submitted"
            ]
            is False
        )


    def test_determinism() -> None:
        request = make_request()
        validation = make_validation(request)

        first = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T15:01:02-05:00"
            ),
            evidence={
                "runtime_adapter_connected": False,
                "live_order_submitted": False,
            },
        )

        second = evaluate_execution_adapter_admission(
            request=request,
            validation=validation,
            admitted_at=(
                "2026-07-10T15:01:02-05:00"
            ),
            evidence={
                "live_order_submitted": False,
                "runtime_adapter_connected": False,
            },
        )

        assert (
            first.admission_id
            == second.admission_id
        )
        assert (
            first.admission_hash
            == second.admission_hash
        )
        assert (
            first.to_dict()
            == second.to_dict()
        )
        assert (
            first.to_canonical_json()
            == second.to_canonical_json()
        )


    def test_immutability() -> None:
        request = make_request()
        validation = make_validation(request)

        admission = (
            evaluate_execution_adapter_admission(
                request=request,
                validation=validation,
                admitted_at=(
                    "2026-07-10T15:01:02-05:00"
                ),
            )
        )

        try:
            admission.status = (
                AdapterAdmissionStatus.BLOCKED
            )
        except (
            FrozenInstanceError,
            AttributeError,
        ):
            pass
        else:
            raise AssertionError(
                "admission dataclass must be immutable"
            )

        try:
            admission.checks[
                "request_id_matches"
            ] = False
        except TypeError:
            pass
        else:
            raise AssertionError(
                "admission checks must be immutable"
            )


    def test_blocked_validation() -> None:
        request = make_request(
            market_id="UNSUPPORTED-001"
        )

        validation = (
            validate_execution_adapter_request(
                request=request,
                registry=make_registry(),
                validated_at=(
                    "2026-07-10T15:01:01-05:00"
                ),
            )
        )

        admission = (
            evaluate_execution_adapter_admission(
                request=request,
                validation=validation,
                admitted_at=(
                    "2026-07-10T15:01:02-05:00"
                ),
            )
        )

        assert (
            admission.status
            is AdapterAdmissionStatus.BLOCKED
        )
        assert (
            "registry_validation_not_approved"
            in admission.reason_codes
        )
        assert admission.execution_allowed is False


    def test_request_mismatch_blocked() -> None:
        first_request = make_request()

        second_request = (
            build_execution_adapter_request(
                authorization_record=(
                    make_authorization_record()
                ),
                adapter_id=(
                    "adapter.kalshi.execution"
                ),
                account_reference=(
                    "account-primary"
                ),
                market_id=(
                    "KXTEST-26JUL11"
                ),
                action="buy",
                order_type="limit",
                quantity="10",
                limit_price="0.42",
                price_unit=(
                    "usd_probability"
                ),
                time_in_force="gtc",
                client_order_id=(
                    "client-order-002"
                ),
                created_at=(
                    "2026-07-10T15:02:00-05:00"
                ),
                expires_at=(
                    "2026-07-10T15:07:00-05:00"
                ),
                rationale=(
                    "Second authorized request."
                ),
            )
        )

        validation = make_validation(
            first_request
        )

        admission = (
            evaluate_execution_adapter_admission(
                request=second_request,
                validation=validation,
                admitted_at=(
                    "2026-07-10T15:02:01-05:00"
                ),
            )
        )

        assert (
            admission.status
            is AdapterAdmissionStatus.BLOCKED
        )
        assert (
            "request_id_mismatch"
            in admission.reason_codes
        )


    def test_caller_supplied_timestamp_required() -> None:
        request = make_request()
        validation = make_validation(request)

        expect_admission_error(
            lambda: (
                evaluate_execution_adapter_admission(
                    request=request,
                    validation=validation,
                    admitted_at=(
                        "2026-07-10T15:01:02"
                    ),
                )
            ),
            "must include a timezone offset",
        )


    def main() -> None:
        test_admitted_contract()
        test_determinism()
        test_immutability()
        test_blocked_validation()
        test_request_mismatch_blocked()
        test_caller_supplied_timestamp_required()

        request = make_request()
        validation = make_validation(request)

        admission = (
            evaluate_execution_adapter_admission(
                request=request,
                validation=validation,
                admitted_at=(
                    "2026-07-10T15:01:02-05:00"
                ),
                evidence={
                    "runtime_adapter_connected": False,
                    "live_order_submitted": False,
                    "exchange_called": False,
                    "funds_moved": False,
                    "portfolio_mutated": False,
                },
            )
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "admission_status": (
                admission.status.value
            ),
            "adapter_id": admission.adapter_id,
            "reason_codes": list(
                admission.reason_codes
            ),
            "read_only": admission.read_only,
            "execution_allowed": (
                admission.execution_allowed
            ),
            "runtime_adapter_required": (
                admission.runtime_adapter_required
            ),
        }

        print(
            "[PASS] INT-018 Q Series "
            "Execution Adapter Admission Gate"
        )
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    '''
    # INT-018 Q Series Execution Adapter Admission Gate
    from .qseries_execution_adapter_admission_gate import (
        AdapterAdmissionStatus,
        ExecutionAdapterAdmission,
        ExecutionAdapterAdmissionError,
        evaluate_execution_adapter_admission,
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
        "# INT-018 Q Series "
        "Execution Adapter Admission Gate"
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
    print(" INT-018 INSTALLER")
    print(" Q Series Execution Adapter Admission Gate")
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
    print("[DONE] INT-018 installed")
    print()
    print("Run:")
    print(
        "py "
        "test_int_018_qseries_execution_adapter_admission_gate.py"
    )


if __name__ == "__main__":
    main()