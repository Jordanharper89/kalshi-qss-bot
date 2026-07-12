from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "integration"
    / "qseries_execution_adapter_contract.py"
)

TEST_PATH = ROOT / "test_int_016_qseries_execution_adapter_contract.py"

PACKAGE_INIT_PATH = ROOT / "qseries_v2" / "integration" / "__init__.py"


MODULE_CONTENT = dedent(
    r'''
    """
    INT-016 — Q Series Execution Adapter Contract.

    This module defines the canonical boundary between the Q Series
    authorization pipeline and future execution adapters.

    Architectural guarantees
    -------------------------
    * Oracle remains read-only intelligence.
    * Q Series remains the owner of authorization.
    * No exchange, broker, portfolio, account, or live order API is called.
    * No funds or positions are mutated.
    * All records are immutable.
    * All identifiers and hashes are deterministic.
    * All timestamps are caller supplied.
    * All hashing uses canonical JSON and never repr().
    * Requests and results are replayable, auditable, and explainable.

    INT-016 is a contract module only. It does not implement an adapter and
    does not grant execution permission.
    """

    from __future__ import annotations

    from dataclasses import dataclass, field
    from datetime import datetime
    from decimal import Decimal, InvalidOperation
    from enum import Enum
    import hashlib
    import json
    from types import MappingProxyType
    from typing import Any, Mapping, Protocol, runtime_checkable


    SCHEMA_VERSION = "INT-016"
    ENGINE_ID = "INT-016"
    SOURCE_AUTHORIZATION_SCHEMA = "INT-015"


    class ExecutionAdapterContractError(ValueError):
        """Raised when an INT-016 execution-adapter contract is invalid."""


    class AdapterAction(str, Enum):
        BUY = "buy"
        SELL = "sell"


    class AdapterOrderType(str, Enum):
        LIMIT = "limit"
        MARKET = "market"


    class AdapterRequestStatus(str, Enum):
        READY_FOR_ADAPTER = "ready_for_adapter"
        BLOCKED = "blocked"


    class AdapterResultStatus(str, Enum):
        NOT_EXECUTED = "not_executed"
        ACCEPTED = "accepted"
        REJECTED = "rejected"
        FAILED = "failed"


    def _require_non_empty_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise ExecutionAdapterContractError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ExecutionAdapterContractError(
                f"{field_name} must not be empty"
            )

        return normalized


    def _require_bool(value: Any, field_name: str) -> bool:
        if not isinstance(value, bool):
            raise ExecutionAdapterContractError(
                f"{field_name} must be a bool"
            )

        return value


    def _normalize_optional_string(
        value: Any,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        return _require_non_empty_string(value, field_name)


    def _normalize_decimal(
        value: Any,
        field_name: str,
        *,
        allow_zero: bool = False,
    ) -> str:
        if isinstance(value, bool):
            raise ExecutionAdapterContractError(
                f"{field_name} must be numeric"
            )

        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ExecutionAdapterContractError(
                f"{field_name} must be a valid decimal"
            ) from exc

        if not decimal_value.is_finite():
            raise ExecutionAdapterContractError(
                f"{field_name} must be finite"
            )

        if allow_zero:
            if decimal_value < 0:
                raise ExecutionAdapterContractError(
                    f"{field_name} must be greater than or equal to zero"
                )
        elif decimal_value <= 0:
            raise ExecutionAdapterContractError(
                f"{field_name} must be greater than zero"
            )

        normalized = format(decimal_value.normalize(), "f")

        if "." in normalized:
            normalized = normalized.rstrip("0").rstrip(".")

        if normalized == "-0":
            normalized = "0"

        return normalized


    def _normalize_timestamp(value: Any, field_name: str) -> str:
        text = _require_non_empty_string(value, field_name)

        parse_value = text

        if parse_value.endswith("Z"):
            parse_value = parse_value[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(parse_value)
        except ValueError as exc:
            raise ExecutionAdapterContractError(
                f"{field_name} must be a valid ISO-8601 timestamp"
            ) from exc

        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ExecutionAdapterContractError(
                f"{field_name} must include a timezone offset"
            )

        return parsed.isoformat()


    def _timestamp_to_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value)


    def _canonicalize(value: Any) -> Any:
        """
        Convert supported values into canonical JSON-safe values.

        Mapping keys are sorted during JSON serialization. Sets and arbitrary
        objects are intentionally unsupported because their ordering or
        representation may not be stable.
        """

        if value is None or isinstance(value, (str, int, bool)):
            return value

        if isinstance(value, float):
            if value != value or value in (float("inf"), float("-inf")):
                raise ExecutionAdapterContractError(
                    "non-finite floats are not canonical"
                )

            return format(Decimal(str(value)).normalize(), "f")

        if isinstance(value, Decimal):
            if not value.is_finite():
                raise ExecutionAdapterContractError(
                    "non-finite decimals are not canonical"
                )

            normalized = format(value.normalize(), "f")

            if "." in normalized:
                normalized = normalized.rstrip("0").rstrip(".")

            return "0" if normalized == "-0" else normalized

        if isinstance(value, Enum):
            return _canonicalize(value.value)

        if isinstance(value, Mapping):
            canonical_mapping: dict[str, Any] = {}

            for key, item in value.items():
                if not isinstance(key, str):
                    raise ExecutionAdapterContractError(
                        "canonical mapping keys must be strings"
                    )

                canonical_mapping[key] = _canonicalize(item)

            return canonical_mapping

        if isinstance(value, (list, tuple)):
            return [_canonicalize(item) for item in value]

        raise ExecutionAdapterContractError(
            f"unsupported canonical value type: {type(value).__name__}"
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
        payload = canonical_json(value).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


    def _freeze_mapping(
        value: Mapping[str, Any] | None,
        field_name: str,
    ) -> Mapping[str, Any]:
        if value is None:
            return MappingProxyType({})

        if not isinstance(value, Mapping):
            raise ExecutionAdapterContractError(
                f"{field_name} must be a mapping"
            )

        canonical_value = _canonicalize(value)

        if not isinstance(canonical_value, dict):
            raise ExecutionAdapterContractError(
                f"{field_name} must resolve to a mapping"
            )

        frozen = json.loads(canonical_json(canonical_value))
        return MappingProxyType(frozen)


    def _mapping_to_dict(value: Mapping[str, Any]) -> dict[str, Any]:
        return json.loads(canonical_json(value))


    def _extract_authorization_id(
        authorization_record: Mapping[str, Any],
    ) -> str:
        candidate_fields = (
            "authorization_id",
            "final_authorization_id",
            "record_id",
            "decision_id",
        )

        for field_name in candidate_fields:
            candidate = authorization_record.get(field_name)

            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()

        return canonical_hash(authorization_record)


    def _extract_authorized_decision(
        authorization_record: Mapping[str, Any],
    ) -> bool:
        direct_fields = (
            "authorized",
            "is_authorized",
            "authorization_granted",
        )

        for field_name in direct_fields:
            value = authorization_record.get(field_name)

            if isinstance(value, bool):
                return value

        textual_fields = (
            "authorization_status",
            "decision",
            "status",
            "outcome",
        )

        authorized_values = {
            "authorized",
            "approved",
            "allow",
            "allowed",
            "pass",
            "passed",
            "ready",
        }

        blocked_values = {
            "blocked",
            "denied",
            "deny",
            "rejected",
            "failed",
            "not_authorized",
        }

        for field_name in textual_fields:
            value = authorization_record.get(field_name)

            if isinstance(value, str):
                normalized = value.strip().lower()

                if normalized in authorized_values:
                    return True

                if normalized in blocked_values:
                    return False

        raise ExecutionAdapterContractError(
            "INT-015 authorization record does not contain a recognizable "
            "authorization decision"
        )


    def _validate_int_015_authorization(
        authorization_record: Mapping[str, Any],
    ) -> tuple[str, str]:
        if not isinstance(authorization_record, Mapping):
            raise ExecutionAdapterContractError(
                "authorization_record must be a mapping"
            )

        canonical_record = _canonicalize(authorization_record)

        if not isinstance(canonical_record, dict):
            raise ExecutionAdapterContractError(
                "authorization_record must resolve to a mapping"
            )

        schema_version = _require_non_empty_string(
            canonical_record.get("schema_version"),
            "authorization_record.schema_version",
        )

        if schema_version != SOURCE_AUTHORIZATION_SCHEMA:
            raise ExecutionAdapterContractError(
                "authorization_record.schema_version must be INT-015"
            )

        adapter_execution_required = _require_bool(
            canonical_record.get("adapter_execution_required"),
            "authorization_record.adapter_execution_required",
        )

        if not adapter_execution_required:
            raise ExecutionAdapterContractError(
                "INT-015 must require execution through an adapter"
            )

        direct_execution_allowed = _require_bool(
            canonical_record.get("execution_allowed"),
            "authorization_record.execution_allowed",
        )

        if direct_execution_allowed:
            raise ExecutionAdapterContractError(
                "INT-015 must not directly allow execution"
            )

        if not _extract_authorized_decision(canonical_record):
            raise ExecutionAdapterContractError(
                "INT-015 authorization decision is not authorized"
            )

        authorization_id = _extract_authorization_id(canonical_record)
        authorization_hash = canonical_hash(canonical_record)

        return authorization_id, authorization_hash


    @dataclass(frozen=True, slots=True)
    class ExecutionAdapterRequest:
        """
        Immutable instruction envelope delivered to a concrete adapter.

        The presence of this request does not mean an order was executed.
        A later approved adapter must independently validate the request and
        return an ExecutionAdapterResult.
        """

        request_id: str
        authorization_id: str
        authorization_record_hash: str
        adapter_id: str
        account_reference: str
        market_id: str
        action: AdapterAction
        order_type: AdapterOrderType
        quantity: str
        limit_price: str | None
        price_unit: str | None
        time_in_force: str
        client_order_id: str
        created_at: str
        expires_at: str
        request_status: AdapterRequestStatus
        rationale: str
        metadata: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        execution_allowed: bool = False
        requires_concrete_adapter: bool = True
        contract_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "request_id",
                _require_non_empty_string(self.request_id, "request_id"),
            )
            object.__setattr__(
                self,
                "authorization_id",
                _require_non_empty_string(
                    self.authorization_id,
                    "authorization_id",
                ),
            )
            object.__setattr__(
                self,
                "authorization_record_hash",
                _require_non_empty_string(
                    self.authorization_record_hash,
                    "authorization_record_hash",
                ),
            )
            object.__setattr__(
                self,
                "adapter_id",
                _require_non_empty_string(self.adapter_id, "adapter_id"),
            )
            object.__setattr__(
                self,
                "account_reference",
                _require_non_empty_string(
                    self.account_reference,
                    "account_reference",
                ),
            )
            object.__setattr__(
                self,
                "market_id",
                _require_non_empty_string(self.market_id, "market_id"),
            )
            object.__setattr__(
                self,
                "quantity",
                _normalize_decimal(self.quantity, "quantity"),
            )
            object.__setattr__(
                self,
                "time_in_force",
                _require_non_empty_string(
                    self.time_in_force,
                    "time_in_force",
                ).lower(),
            )
            object.__setattr__(
                self,
                "client_order_id",
                _require_non_empty_string(
                    self.client_order_id,
                    "client_order_id",
                ),
            )
            object.__setattr__(
                self,
                "created_at",
                _normalize_timestamp(self.created_at, "created_at"),
            )
            object.__setattr__(
                self,
                "expires_at",
                _normalize_timestamp(self.expires_at, "expires_at"),
            )
            object.__setattr__(
                self,
                "rationale",
                _require_non_empty_string(self.rationale, "rationale"),
            )

            if not isinstance(self.action, AdapterAction):
                object.__setattr__(
                    self,
                    "action",
                    AdapterAction(str(self.action).strip().lower()),
                )

            if not isinstance(self.order_type, AdapterOrderType):
                object.__setattr__(
                    self,
                    "order_type",
                    AdapterOrderType(str(self.order_type).strip().lower()),
                )

            if not isinstance(self.request_status, AdapterRequestStatus):
                object.__setattr__(
                    self,
                    "request_status",
                    AdapterRequestStatus(
                        str(self.request_status).strip().lower()
                    ),
                )

            normalized_price = _normalize_optional_string(
                self.limit_price,
                "limit_price",
            )

            normalized_price_unit = _normalize_optional_string(
                self.price_unit,
                "price_unit",
            )

            if self.order_type is AdapterOrderType.LIMIT:
                if normalized_price is None:
                    raise ExecutionAdapterContractError(
                        "limit_price is required for limit orders"
                    )

                if normalized_price_unit is None:
                    raise ExecutionAdapterContractError(
                        "price_unit is required when limit_price is supplied"
                    )

                normalized_price = _normalize_decimal(
                    normalized_price,
                    "limit_price",
                    allow_zero=True,
                )

            elif normalized_price is not None:
                raise ExecutionAdapterContractError(
                    "market orders must not contain limit_price"
                )

            elif normalized_price_unit is not None:
                raise ExecutionAdapterContractError(
                    "market orders must not contain price_unit"
                )

            object.__setattr__(self, "limit_price", normalized_price)
            object.__setattr__(self, "price_unit", normalized_price_unit)

            created = _timestamp_to_datetime(self.created_at)
            expires = _timestamp_to_datetime(self.expires_at)

            if expires <= created:
                raise ExecutionAdapterContractError(
                    "expires_at must be later than created_at"
                )

            if self.schema_version != SCHEMA_VERSION:
                raise ExecutionAdapterContractError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise ExecutionAdapterContractError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise ExecutionAdapterContractError(
                    "INT-016 contract records must be read_only"
                )

            if self.execution_allowed is not False:
                raise ExecutionAdapterContractError(
                    "INT-016 must not directly allow execution"
                )

            if self.requires_concrete_adapter is not True:
                raise ExecutionAdapterContractError(
                    "INT-016 must require a concrete adapter"
                )

            object.__setattr__(
                self,
                "metadata",
                _freeze_mapping(self.metadata, "metadata"),
            )

            calculated_hash = canonical_hash(self._hash_payload())

            if self.contract_hash:
                supplied_hash = _require_non_empty_string(
                    self.contract_hash,
                    "contract_hash",
                )

                if supplied_hash != calculated_hash:
                    raise ExecutionAdapterContractError(
                        "contract_hash does not match request contents"
                    )

            object.__setattr__(self, "contract_hash", calculated_hash)

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "request_id": self.request_id,
                "authorization_id": self.authorization_id,
                "authorization_record_hash": (
                    self.authorization_record_hash
                ),
                "adapter_id": self.adapter_id,
                "account_reference": self.account_reference,
                "market_id": self.market_id,
                "action": self.action.value,
                "order_type": self.order_type.value,
                "quantity": self.quantity,
                "limit_price": self.limit_price,
                "price_unit": self.price_unit,
                "time_in_force": self.time_in_force,
                "client_order_id": self.client_order_id,
                "created_at": self.created_at,
                "expires_at": self.expires_at,
                "request_status": self.request_status.value,
                "rationale": self.rationale,
                "metadata": _mapping_to_dict(self.metadata),
                "read_only": self.read_only,
                "execution_allowed": self.execution_allowed,
                "requires_concrete_adapter": (
                    self.requires_concrete_adapter
                ),
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["contract_hash"] = self.contract_hash
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(self.to_dict())


    @dataclass(frozen=True, slots=True)
    class ExecutionAdapterResult:
        """
        Immutable adapter-result envelope.

        A future concrete adapter returns this record after processing an
        ExecutionAdapterRequest. INT-016 itself never creates live orders.
        """

        result_id: str
        request_id: str
        adapter_id: str
        status: AdapterResultStatus
        processed_at: str
        adapter_reference: str | None
        executed_quantity: str
        average_price: str | None
        price_unit: str | None
        reason_code: str
        explanation: str
        details: Mapping[str, Any] = field(
            default_factory=lambda: MappingProxyType({})
        )
        schema_version: str = SCHEMA_VERSION
        engine_id: str = ENGINE_ID
        read_only: bool = True
        result_hash: str = ""

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "result_id",
                _require_non_empty_string(self.result_id, "result_id"),
            )
            object.__setattr__(
                self,
                "request_id",
                _require_non_empty_string(self.request_id, "request_id"),
            )
            object.__setattr__(
                self,
                "adapter_id",
                _require_non_empty_string(self.adapter_id, "adapter_id"),
            )
            object.__setattr__(
                self,
                "processed_at",
                _normalize_timestamp(self.processed_at, "processed_at"),
            )
            object.__setattr__(
                self,
                "reason_code",
                _require_non_empty_string(
                    self.reason_code,
                    "reason_code",
                ).lower(),
            )
            object.__setattr__(
                self,
                "explanation",
                _require_non_empty_string(
                    self.explanation,
                    "explanation",
                ),
            )

            if not isinstance(self.status, AdapterResultStatus):
                object.__setattr__(
                    self,
                    "status",
                    AdapterResultStatus(str(self.status).strip().lower()),
                )

            adapter_reference = _normalize_optional_string(
                self.adapter_reference,
                "adapter_reference",
            )
            object.__setattr__(
                self,
                "adapter_reference",
                adapter_reference,
            )

            executed_quantity = _normalize_decimal(
                self.executed_quantity,
                "executed_quantity",
                allow_zero=True,
            )
            object.__setattr__(
                self,
                "executed_quantity",
                executed_quantity,
            )

            average_price = _normalize_optional_string(
                self.average_price,
                "average_price",
            )
            price_unit = _normalize_optional_string(
                self.price_unit,
                "price_unit",
            )

            if average_price is not None:
                average_price = _normalize_decimal(
                    average_price,
                    "average_price",
                    allow_zero=True,
                )

                if price_unit is None:
                    raise ExecutionAdapterContractError(
                        "price_unit is required when average_price is supplied"
                    )
            elif price_unit is not None:
                raise ExecutionAdapterContractError(
                    "price_unit requires average_price"
                )

            object.__setattr__(self, "average_price", average_price)
            object.__setattr__(self, "price_unit", price_unit)

            if (
                self.status is AdapterResultStatus.NOT_EXECUTED
                and executed_quantity != "0"
            ):
                raise ExecutionAdapterContractError(
                    "not_executed results must have executed_quantity zero"
                )

            if (
                self.status
                in {
                    AdapterResultStatus.REJECTED,
                    AdapterResultStatus.FAILED,
                }
                and executed_quantity != "0"
            ):
                raise ExecutionAdapterContractError(
                    "rejected or failed results must have "
                    "executed_quantity zero"
                )

            if self.schema_version != SCHEMA_VERSION:
                raise ExecutionAdapterContractError(
                    f"schema_version must be {SCHEMA_VERSION}"
                )

            if self.engine_id != ENGINE_ID:
                raise ExecutionAdapterContractError(
                    f"engine_id must be {ENGINE_ID}"
                )

            if self.read_only is not True:
                raise ExecutionAdapterContractError(
                    "INT-016 result records must be read_only"
                )

            object.__setattr__(
                self,
                "details",
                _freeze_mapping(self.details, "details"),
            )

            calculated_hash = canonical_hash(self._hash_payload())

            if self.result_hash:
                supplied_hash = _require_non_empty_string(
                    self.result_hash,
                    "result_hash",
                )

                if supplied_hash != calculated_hash:
                    raise ExecutionAdapterContractError(
                        "result_hash does not match result contents"
                    )

            object.__setattr__(self, "result_hash", calculated_hash)

        def _hash_payload(self) -> dict[str, Any]:
            return {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "result_id": self.result_id,
                "request_id": self.request_id,
                "adapter_id": self.adapter_id,
                "status": self.status.value,
                "processed_at": self.processed_at,
                "adapter_reference": self.adapter_reference,
                "executed_quantity": self.executed_quantity,
                "average_price": self.average_price,
                "price_unit": self.price_unit,
                "reason_code": self.reason_code,
                "explanation": self.explanation,
                "details": _mapping_to_dict(self.details),
                "read_only": self.read_only,
            }

        def to_dict(self) -> dict[str, Any]:
            payload = self._hash_payload()
            payload["result_hash"] = self.result_hash
            return payload

        def to_canonical_json(self) -> str:
            return canonical_json(self.to_dict())


    @runtime_checkable
    class ExecutionAdapterProtocol(Protocol):
        """
        Structural contract for a future concrete execution adapter.

        Implementations may perform execution only after that subsystem is
        separately approved. INT-016 supplies no implementation.
        """

        adapter_id: str

        def process(
            self,
            request: ExecutionAdapterRequest,
        ) -> ExecutionAdapterResult:
            ...


    def build_execution_adapter_request(
        *,
        authorization_record: Mapping[str, Any],
        adapter_id: str,
        account_reference: str,
        market_id: str,
        action: AdapterAction | str,
        order_type: AdapterOrderType | str,
        quantity: Any,
        limit_price: Any | None,
        price_unit: str | None,
        time_in_force: str,
        client_order_id: str,
        created_at: str,
        expires_at: str,
        rationale: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> ExecutionAdapterRequest:
        """
        Build a deterministic adapter request from an authorized INT-015 record.

        The generated request is still non-executing. It only establishes the
        canonical instruction that a later concrete adapter may process.
        """

        canonical_authorization = _canonicalize(authorization_record)

        if not isinstance(canonical_authorization, dict):
            raise ExecutionAdapterContractError(
                "authorization_record must resolve to a mapping"
            )

        authorization_id, authorization_hash = (
            _validate_int_015_authorization(canonical_authorization)
        )

        normalized_adapter_id = _require_non_empty_string(
            adapter_id,
            "adapter_id",
        )
        normalized_account_reference = _require_non_empty_string(
            account_reference,
            "account_reference",
        )
        normalized_market_id = _require_non_empty_string(
            market_id,
            "market_id",
        )
        normalized_client_order_id = _require_non_empty_string(
            client_order_id,
            "client_order_id",
        )
        normalized_created_at = _normalize_timestamp(
            created_at,
            "created_at",
        )
        normalized_expires_at = _normalize_timestamp(
            expires_at,
            "expires_at",
        )
        normalized_rationale = _require_non_empty_string(
            rationale,
            "rationale",
        )
        normalized_quantity = _normalize_decimal(quantity, "quantity")

        normalized_action = (
            action
            if isinstance(action, AdapterAction)
            else AdapterAction(str(action).strip().lower())
        )

        normalized_order_type = (
            order_type
            if isinstance(order_type, AdapterOrderType)
            else AdapterOrderType(str(order_type).strip().lower())
        )

        normalized_limit_price: str | None

        if limit_price is None:
            normalized_limit_price = None
        else:
            normalized_limit_price = _normalize_decimal(
                limit_price,
                "limit_price",
                allow_zero=True,
            )

        normalized_price_unit = _normalize_optional_string(
            price_unit,
            "price_unit",
        )

        normalized_time_in_force = _require_non_empty_string(
            time_in_force,
            "time_in_force",
        ).lower()

        frozen_metadata = _freeze_mapping(metadata, "metadata")

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "authorization_id": authorization_id,
            "authorization_record_hash": authorization_hash,
            "adapter_id": normalized_adapter_id,
            "account_reference": normalized_account_reference,
            "market_id": normalized_market_id,
            "action": normalized_action.value,
            "order_type": normalized_order_type.value,
            "quantity": normalized_quantity,
            "limit_price": normalized_limit_price,
            "price_unit": normalized_price_unit,
            "time_in_force": normalized_time_in_force,
            "client_order_id": normalized_client_order_id,
            "created_at": normalized_created_at,
            "expires_at": normalized_expires_at,
            "rationale": normalized_rationale,
            "metadata": _mapping_to_dict(frozen_metadata),
        }

        request_id = f"int016-{canonical_hash(identity_payload)[:32]}"

        return ExecutionAdapterRequest(
            request_id=request_id,
            authorization_id=authorization_id,
            authorization_record_hash=authorization_hash,
            adapter_id=normalized_adapter_id,
            account_reference=normalized_account_reference,
            market_id=normalized_market_id,
            action=normalized_action,
            order_type=normalized_order_type,
            quantity=normalized_quantity,
            limit_price=normalized_limit_price,
            price_unit=normalized_price_unit,
            time_in_force=normalized_time_in_force,
            client_order_id=normalized_client_order_id,
            created_at=normalized_created_at,
            expires_at=normalized_expires_at,
            request_status=AdapterRequestStatus.READY_FOR_ADAPTER,
            rationale=normalized_rationale,
            metadata=frozen_metadata,
        )


    def build_not_executed_result(
        *,
        request: ExecutionAdapterRequest,
        processed_at: str,
        reason_code: str,
        explanation: str,
        details: Mapping[str, Any] | None = None,
    ) -> ExecutionAdapterResult:
        """
        Create a deterministic result proving that no execution occurred.

        This is useful for dry runs, unavailable adapters, policy blocks, and
        replay validation.
        """

        if not isinstance(request, ExecutionAdapterRequest):
            raise ExecutionAdapterContractError(
                "request must be an ExecutionAdapterRequest"
            )

        normalized_processed_at = _normalize_timestamp(
            processed_at,
            "processed_at",
        )
        normalized_reason_code = _require_non_empty_string(
            reason_code,
            "reason_code",
        ).lower()
        normalized_explanation = _require_non_empty_string(
            explanation,
            "explanation",
        )
        frozen_details = _freeze_mapping(details, "details")

        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "request_id": request.request_id,
            "adapter_id": request.adapter_id,
            "status": AdapterResultStatus.NOT_EXECUTED.value,
            "processed_at": normalized_processed_at,
            "reason_code": normalized_reason_code,
            "explanation": normalized_explanation,
            "details": _mapping_to_dict(frozen_details),
        }

        result_id = f"int016-result-{canonical_hash(identity_payload)[:32]}"

        return ExecutionAdapterResult(
            result_id=result_id,
            request_id=request.request_id,
            adapter_id=request.adapter_id,
            status=AdapterResultStatus.NOT_EXECUTED,
            processed_at=normalized_processed_at,
            adapter_reference=None,
            executed_quantity="0",
            average_price=None,
            price_unit=None,
            reason_code=normalized_reason_code,
            explanation=normalized_explanation,
            details=frozen_details,
        )


    __all__ = [
        "SCHEMA_VERSION",
        "ENGINE_ID",
        "SOURCE_AUTHORIZATION_SCHEMA",
        "ExecutionAdapterContractError",
        "AdapterAction",
        "AdapterOrderType",
        "AdapterRequestStatus",
        "AdapterResultStatus",
        "ExecutionAdapterRequest",
        "ExecutionAdapterResult",
        "ExecutionAdapterProtocol",
        "canonical_json",
        "canonical_hash",
        "build_execution_adapter_request",
        "build_not_executed_result",
    ]
    '''
).lstrip()


TEST_CONTENT = dedent(
    r'''
    from __future__ import annotations

    from dataclasses import FrozenInstanceError
    import json

    from qseries_v2.integration.qseries_execution_adapter_contract import (
        AdapterAction,
        AdapterOrderType,
        AdapterRequestStatus,
        AdapterResultStatus,
        ENGINE_ID,
        SCHEMA_VERSION,
        ExecutionAdapterContractError,
        build_execution_adapter_request,
        build_not_executed_result,
        canonical_hash,
        canonical_json,
    )


    def expect_contract_error(callable_object, expected_text: str) -> None:
        try:
            callable_object()
        except ExecutionAdapterContractError as exc:
            assert expected_text in str(exc), (
                f"expected error containing {expected_text!r}, got {exc!r}"
            )
        else:
            raise AssertionError(
                f"expected ExecutionAdapterContractError containing "
                f"{expected_text!r}"
            )


    def make_authorization_record() -> dict:
        return {
            "schema_version": "INT-015",
            "engine_id": "INT-015",
            "authorization_id": "final-auth-0001",
            "authorization_status": "authorized",
            "opportunity_id": "opp-001",
            "read_only": True,
            "execution_allowed": False,
            "adapter_execution_required": True,
            "authorized_at": "2026-07-10T15:00:00-05:00",
            "explanation": {
                "gate": "final execution authorization",
                "decision": "all required checks passed",
            },
        }


    def build_request():
        return build_execution_adapter_request(
            authorization_record=make_authorization_record(),
            adapter_id="adapter.kalshi.execution",
            account_reference="account-primary",
            market_id="KXTEST-26JUL10",
            action=AdapterAction.BUY,
            order_type=AdapterOrderType.LIMIT,
            quantity="12.000",
            limit_price="0.43",
            price_unit="usd_probability",
            time_in_force="GTC",
            client_order_id="qseries-client-order-001",
            created_at="2026-07-10T15:01:00-05:00",
            expires_at="2026-07-10T15:06:00-05:00",
            rationale=(
                "INT-015 granted final authorization and requires processing "
                "through an approved execution adapter."
            ),
            metadata={
                "strategy_id": "strategy.test",
                "replay_sequence": 16,
                "tags": ["integration", "dry-run"],
            },
        )


    def test_canonical_hashing() -> None:
        first = {
            "b": 2,
            "a": {
                "z": "last",
                "y": [3, 2, 1],
            },
        }

        second = {
            "a": {
                "y": [3, 2, 1],
                "z": "last",
            },
            "b": 2,
        }

        assert canonical_json(first) == canonical_json(second)
        assert canonical_hash(first) == canonical_hash(second)


    def test_request_contract() -> None:
        request = build_request()

        assert request.schema_version == SCHEMA_VERSION
        assert request.engine_id == ENGINE_ID
        assert request.request_id.startswith("int016-")
        assert request.authorization_id == "final-auth-0001"
        assert len(request.authorization_record_hash) == 64
        assert request.adapter_id == "adapter.kalshi.execution"
        assert request.account_reference == "account-primary"
        assert request.market_id == "KXTEST-26JUL10"
        assert request.action is AdapterAction.BUY
        assert request.order_type is AdapterOrderType.LIMIT
        assert request.quantity == "12"
        assert request.limit_price == "0.43"
        assert request.price_unit == "usd_probability"
        assert request.time_in_force == "gtc"
        assert request.request_status is AdapterRequestStatus.READY_FOR_ADAPTER
        assert request.read_only is True
        assert request.execution_allowed is False
        assert request.requires_concrete_adapter is True
        assert len(request.contract_hash) == 64

        payload = request.to_dict()

        assert payload["schema_version"] == "INT-016"
        assert payload["execution_allowed"] is False
        assert payload["requires_concrete_adapter"] is True
        assert payload["contract_hash"] == request.contract_hash

        decoded = json.loads(request.to_canonical_json())
        assert decoded == payload


    def test_determinism() -> None:
        first = build_request()
        second = build_request()

        assert first.request_id == second.request_id
        assert first.contract_hash == second.contract_hash
        assert first.to_dict() == second.to_dict()
        assert first.to_canonical_json() == second.to_canonical_json()


    def test_immutability() -> None:
        request = build_request()

        try:
            request.market_id = "MUTATED"
        except (FrozenInstanceError, AttributeError):
            pass
        else:
            raise AssertionError("request dataclass must be immutable")

        try:
            request.metadata["strategy_id"] = "mutated"
        except TypeError:
            pass
        else:
            raise AssertionError("request metadata must be immutable")


    def test_not_executed_result() -> None:
        request = build_request()

        result = build_not_executed_result(
            request=request,
            processed_at="2026-07-10T15:01:01-05:00",
            reason_code="contract_only",
            explanation=(
                "INT-016 defines the adapter boundary but contains no live "
                "execution implementation."
            ),
            details={
                "live_order_submitted": False,
                "portfolio_mutated": False,
                "funds_moved": False,
            },
        )

        duplicate = build_not_executed_result(
            request=request,
            processed_at="2026-07-10T15:01:01-05:00",
            reason_code="contract_only",
            explanation=(
                "INT-016 defines the adapter boundary but contains no live "
                "execution implementation."
            ),
            details={
                "live_order_submitted": False,
                "portfolio_mutated": False,
                "funds_moved": False,
            },
        )

        assert result.status is AdapterResultStatus.NOT_EXECUTED
        assert result.executed_quantity == "0"
        assert result.adapter_reference is None
        assert result.average_price is None
        assert result.read_only is True
        assert result.result_id == duplicate.result_id
        assert result.result_hash == duplicate.result_hash
        assert result.to_dict() == duplicate.to_dict()
        assert result.details["live_order_submitted"] is False
        assert result.details["portfolio_mutated"] is False
        assert result.details["funds_moved"] is False


    def test_authorization_boundary_rejections() -> None:
        blocked = make_authorization_record()
        blocked["authorization_status"] = "blocked"

        expect_contract_error(
            lambda: build_execution_adapter_request(
                authorization_record=blocked,
                adapter_id="adapter.test",
                account_reference="account.test",
                market_id="market.test",
                action="buy",
                order_type="limit",
                quantity="1",
                limit_price="0.50",
                price_unit="probability",
                time_in_force="gtc",
                client_order_id="client-1",
                created_at="2026-07-10T15:01:00-05:00",
                expires_at="2026-07-10T15:02:00-05:00",
                rationale="test",
            ),
            "not authorized",
        )

        wrong_schema = make_authorization_record()
        wrong_schema["schema_version"] = "INT-014"

        expect_contract_error(
            lambda: build_execution_adapter_request(
                authorization_record=wrong_schema,
                adapter_id="adapter.test",
                account_reference="account.test",
                market_id="market.test",
                action="buy",
                order_type="limit",
                quantity="1",
                limit_price="0.50",
                price_unit="probability",
                time_in_force="gtc",
                client_order_id="client-1",
                created_at="2026-07-10T15:01:00-05:00",
                expires_at="2026-07-10T15:02:00-05:00",
                rationale="test",
            ),
            "must be INT-015",
        )

        direct_execution = make_authorization_record()
        direct_execution["execution_allowed"] = True

        expect_contract_error(
            lambda: build_execution_adapter_request(
                authorization_record=direct_execution,
                adapter_id="adapter.test",
                account_reference="account.test",
                market_id="market.test",
                action="buy",
                order_type="limit",
                quantity="1",
                limit_price="0.50",
                price_unit="probability",
                time_in_force="gtc",
                client_order_id="client-1",
                created_at="2026-07-10T15:01:00-05:00",
                expires_at="2026-07-10T15:02:00-05:00",
                rationale="test",
            ),
            "must not directly allow execution",
        )


    def test_timestamp_and_order_validation() -> None:
        expect_contract_error(
            lambda: build_execution_adapter_request(
                authorization_record=make_authorization_record(),
                adapter_id="adapter.test",
                account_reference="account.test",
                market_id="market.test",
                action="buy",
                order_type="limit",
                quantity="1",
                limit_price="0.50",
                price_unit="probability",
                time_in_force="gtc",
                client_order_id="client-1",
                created_at="2026-07-10T15:01:00",
                expires_at="2026-07-10T15:02:00-05:00",
                rationale="test",
            ),
            "must include a timezone offset",
        )

        expect_contract_error(
            lambda: build_execution_adapter_request(
                authorization_record=make_authorization_record(),
                adapter_id="adapter.test",
                account_reference="account.test",
                market_id="market.test",
                action="buy",
                order_type="market",
                quantity="1",
                limit_price="0.50",
                price_unit="probability",
                time_in_force="ioc",
                client_order_id="client-1",
                created_at="2026-07-10T15:01:00-05:00",
                expires_at="2026-07-10T15:02:00-05:00",
                rationale="test",
            ),
            "market orders must not contain limit_price",
        )

        expect_contract_error(
            lambda: build_execution_adapter_request(
                authorization_record=make_authorization_record(),
                adapter_id="adapter.test",
                account_reference="account.test",
                market_id="market.test",
                action="buy",
                order_type="limit",
                quantity="0",
                limit_price="0.50",
                price_unit="probability",
                time_in_force="gtc",
                client_order_id="client-1",
                created_at="2026-07-10T15:01:00-05:00",
                expires_at="2026-07-10T15:02:00-05:00",
                rationale="test",
            ),
            "quantity must be greater than zero",
        )


    def main() -> None:
        test_canonical_hashing()
        test_request_contract()
        test_determinism()
        test_immutability()
        test_not_executed_result()
        test_authorization_boundary_rejections()
        test_timestamp_and_order_validation()

        request = build_request()

        result = build_not_executed_result(
            request=request,
            processed_at="2026-07-10T15:01:01-05:00",
            reason_code="contract_only",
            explanation=(
                "Execution adapter contract validated without performing "
                "execution."
            ),
            details={
                "live_order_submitted": False,
                "exchange_called": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        )

        summary = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "request_id": request.request_id,
            "request_status": request.request_status.value,
            "adapter_id": request.adapter_id,
            "result_status": result.status.value,
            "read_only": request.read_only,
            "execution_allowed": request.execution_allowed,
            "requires_concrete_adapter": (
                request.requires_concrete_adapter
            ),
        }

        print("[PASS] INT-016 Q Series Execution Adapter Contract")
        print(summary)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


EXPORT_BLOCK = dedent(
    '''
    # INT-016 Q Series Execution Adapter Contract
    from .qseries_execution_adapter_contract import (
        AdapterAction,
        AdapterOrderType,
        AdapterRequestStatus,
        AdapterResultStatus,
        ExecutionAdapterContractError,
        ExecutionAdapterProtocol,
        ExecutionAdapterRequest,
        ExecutionAdapterResult,
        build_execution_adapter_request,
        build_not_executed_result,
    )
    '''
).strip()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"[OK] Wrote {path}")


def update_package_exports(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = path.read_text(encoding="utf-8") if path.exists() else ""

    marker = "# INT-016 Q Series Execution Adapter Contract"

    if marker in existing:
        print(f"[OK] Export already present in {path}")
        return

    updated = existing.rstrip()

    if updated:
        updated += "\n\n"

    updated += EXPORT_BLOCK + "\n"

    path.write_text(updated, encoding="utf-8", newline="\n")
    print(f"[OK] Updated {path}")


def main() -> None:
    print("========================================")
    print(" INT-016 INSTALLER")
    print(" Q Series Execution Adapter Contract")
    print("========================================")

    write_file(MODULE_PATH, MODULE_CONTENT)
    write_file(TEST_PATH, TEST_CONTENT)
    update_package_exports(PACKAGE_INIT_PATH)

    print()
    print("[DONE] INT-016 installed")
    print()
    print("Run:")
    print("py test_int_016_qseries_execution_adapter_contract.py")


if __name__ == "__main__":
    main()