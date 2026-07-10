
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .market_regime_discovery_contract import (
    MarketRegimeDiscoveryResult,
    validate_market_regime_discovery_result,
)

from .market_regime_discovery_engine import (
    MarketRegimeEngineConfig,
    discover_market_regimes,
)


READ_ONLY = True
SCHEMA_VERSION = "RGD-004"

ENGINE_ID = (
    "oracle.discovery.market_regime."
    "pipeline_gate"
)

ACCEPTED_SOURCE_STATUSES = frozenset(
    {
        "ok",
        "empty",
    }
)

ACCEPTED_DISCOVERY_STATUSES = frozenset(
    {
        "ok",
        "empty",
    }
)

GATE_STATUSES = frozenset(
    {
        "accepted",
        "empty",
        "rejected",
    }
)


def _stable_value(
    value: Any,
) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _stable_value(value[key])
            for key in sorted(
                value.keys(),
                key=str,
            )
        }

    if isinstance(value, tuple):
        return tuple(
            _stable_value(item)
            for item in value
        )

    if isinstance(value, list):
        return tuple(
            _stable_value(item)
            for item in value
        )

    if isinstance(value, set):
        return tuple(
            sorted(
                (
                    _stable_value(item)
                    for item in value
                ),
                key=repr,
            )
        )

    if hasattr(value, "as_dict") and callable(
        value.as_dict
    ):
        return _stable_value(
            value.as_dict()
        )

    return value


def _stable_hash(
    value: Any,
) -> str:
    return sha256(
        repr(
            _stable_value(value)
        ).encode("utf-8")
    ).hexdigest()


def _read_value(
    value: Any,
    key: str,
    default: Any = None,
) -> Any:
    if isinstance(value, Mapping):
        return value.get(
            key,
            default,
        )

    return getattr(
        value,
        key,
        default,
    )


def _first_value(
    value: Any,
    keys: Sequence[str],
    default: Any = None,
) -> Any:
    for key in keys:
        result = _read_value(
            value,
            key,
            None,
        )

        if result is not None:
            return result

    return default


def _extract_records(
    source_result: Any,
) -> Tuple[Any, ...]:
    records = _first_value(
        source_result,
        (
            "records",
            "signals",
            "items",
            "observations",
            "source_records",
        ),
        tuple(),
    )

    if records is None:
        return tuple()

    return tuple(records)


def _extract_record_id(
    record: Any,
    index: int,
) -> str:
    value = _first_value(
        record,
        (
            "signal_id",
            "record_id",
            "source_id",
            "id",
        ),
        None,
    )

    if value is None:
        return f"record-index-{index}"

    normalized = str(value).strip()

    if not normalized:
        return f"record-index-{index}"

    return normalized



def _canonical_source_payload(
    source_result: Any,
) -> Dict[str, Any]:
    if (
        hasattr(source_result, "as_dict")
        and callable(source_result.as_dict)
    ):
        raw_payload = source_result.as_dict()
    elif isinstance(source_result, Mapping):
        raw_payload = dict(source_result)
    else:
        raw_payload = _stable_value(
            source_result
        )

    if isinstance(raw_payload, Mapping):
        payload = {
            str(key): _stable_value(value)
            for key, value in sorted(
                raw_payload.items(),
                key=lambda item: str(
                    item[0]
                ),
            )
        }
    else:
        payload = {
            "value": _stable_value(
                raw_payload
            )
        }

    records = _extract_records(
        source_result
    )

    canonical_records = tuple(
        sorted(
            (
                _stable_value(record)
                for record in records
            ),
            key=repr,
        )
    )

    record_keys = (
        "records",
        "signals",
        "items",
        "observations",
        "source_records",
    )

    replaced = False

    for key in record_keys:
        if key in payload:
            payload[key] = canonical_records
            replaced = True
            break

    if records and not replaced:
        payload["records"] = (
            canonical_records
        )

    return {
        str(key): _stable_value(value)
        for key, value in sorted(
            payload.items(),
            key=lambda item: str(
                item[0]
            ),
        )
    }



def _resolve_observed_at(
    source_result: Any,
    observed_at: Optional[str],
) -> str:
    if observed_at is not None:
        resolved = str(observed_at).strip()

        if not resolved:
            raise ValueError(
                "observed_at must not be empty"
            )

        return resolved

    source_time = _first_value(
        source_result,
        (
            "observed_at",
            "generated_at",
            "as_of",
            "captured_at",
        ),
        None,
    )

    if source_time is not None:
        resolved = str(source_time).strip()

        if resolved:
            return resolved

    records = _extract_records(
        source_result
    )

    timestamps = sorted(
        {
            str(
                _first_value(
                    record,
                    (
                        "observed_at",
                        "timestamp",
                        "as_of",
                        "captured_at",
                    ),
                    "",
                )
            ).strip()
            for record in records
            if str(
                _first_value(
                    record,
                    (
                        "observed_at",
                        "timestamp",
                        "as_of",
                        "captured_at",
                    ),
                    "",
                )
            ).strip()
        }
    )

    if timestamps:
        return timestamps[-1]

    return "1970-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class MarketRegimePipelineGateCheck:
    check_id: str
    accepted: bool
    explanation: str
    details: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not str(self.check_id).strip():
            raise ValueError(
                "check_id must not be empty"
            )

        if not str(self.explanation).strip():
            raise ValueError(
                "explanation must not be empty"
            )

        normalized_details = tuple(
            sorted(
                (
                    (
                        str(key),
                        _stable_value(value),
                    )
                    for key, value
                    in self.details
                ),
                key=lambda item: item[0],
            )
        )

        object.__setattr__(
            self,
            "details",
            normalized_details,
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "accepted": self.accepted,
            "explanation": self.explanation,
            "details": {
                key: _stable_value(value)
                for key, value
                in self.details
            },
        }


@dataclass(frozen=True)
class MarketRegimePipelineGateResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    observed_at: str
    source_schema_version: str
    source_engine_id: str
    source_status: str
    source_record_count: int
    discovery_schema_version: str
    discovery_engine_id: str
    discovery_status: str
    opportunity_count: int
    checks: Tuple[
        MarketRegimePipelineGateCheck,
        ...,
    ]
    rejection_reasons: Tuple[str, ...]
    source_hash: str
    discovery_hash: str
    gate_hash: str
    read_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                "invalid gate schema_version"
            )

        if self.engine_id != ENGINE_ID:
            raise ValueError(
                "invalid gate engine_id"
            )

        if self.status not in GATE_STATUSES:
            raise ValueError(
                "invalid gate status"
            )

        if not str(self.observed_at).strip():
            raise ValueError(
                "observed_at must not be empty"
            )

        if self.source_record_count < 0:
            raise ValueError(
                "source_record_count cannot "
                "be negative"
            )

        if self.opportunity_count < 0:
            raise ValueError(
                "opportunity_count cannot "
                "be negative"
            )

        if self.read_only is not True:
            raise ValueError(
                "pipeline gate must be "
                "read-only"
            )

        if self.accepted:
            if self.status not in {
                "accepted",
                "empty",
            }:
                raise ValueError(
                    "accepted gate must have "
                    "accepted or empty status"
                )

            if self.rejection_reasons:
                raise ValueError(
                    "accepted gate cannot have "
                    "rejection reasons"
                )

        else:
            if self.status != "rejected":
                raise ValueError(
                    "rejected gate must have "
                    "rejected status"
                )

            if not self.rejection_reasons:
                raise ValueError(
                    "rejected gate must include "
                    "rejection reasons"
                )

        check_ids = [
            check.check_id
            for check in self.checks
        ]

        if len(check_ids) != len(
            set(check_ids)
        ):
            raise ValueError(
                "gate check identifiers must "
                "be unique"
            )

        if not str(self.source_hash).strip():
            raise ValueError(
                "source_hash must not be empty"
            )

        if not str(self.discovery_hash).strip():
            raise ValueError(
                "discovery_hash must not be "
                "empty"
            )

        if not str(self.gate_hash).strip():
            raise ValueError(
                "gate_hash must not be empty"
            )

    def payload(self) -> Dict[str, Any]:
        return {
            "schema_version": (
                self.schema_version
            ),
            "engine_id": self.engine_id,
            "status": self.status,
            "accepted": self.accepted,
            "observed_at": self.observed_at,
            "source_schema_version": (
                self.source_schema_version
            ),
            "source_engine_id": (
                self.source_engine_id
            ),
            "source_status": (
                self.source_status
            ),
            "source_record_count": (
                self.source_record_count
            ),
            "discovery_schema_version": (
                self.discovery_schema_version
            ),
            "discovery_engine_id": (
                self.discovery_engine_id
            ),
            "discovery_status": (
                self.discovery_status
            ),
            "opportunity_count": (
                self.opportunity_count
            ),
            "checks": tuple(
                check.as_dict()
                for check in self.checks
            ),
            "rejection_reasons": (
                self.rejection_reasons
            ),
            "source_hash": self.source_hash,
            "discovery_hash": (
                self.discovery_hash
            ),
            "read_only": self.read_only,
        }

    def as_dict(self) -> Dict[str, Any]:
        payload = self.payload()

        payload["gate_hash"] = self.gate_hash

        return payload

    def verify_gate_hash(self) -> bool:
        return self.gate_hash == _stable_hash(
            self.payload()
        )


def _make_check(
    check_id: str,
    accepted: bool,
    explanation: str,
    details: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimePipelineGateCheck:
    normalized_details = tuple(
        (
            str(key),
            _stable_value(value),
        )
        for key, value in sorted(
            dict(
                details or {}
            ).items(),
            key=lambda item: str(
                item[0]
            ),
        )
    )

    return MarketRegimePipelineGateCheck(
        check_id=check_id,
        accepted=bool(accepted),
        explanation=str(explanation),
        details=normalized_details,
    )


def _validate_source_result(
    source_result: Any,
) -> Tuple[
    Tuple[
        MarketRegimePipelineGateCheck,
        ...,
    ],
    Tuple[str, ...],
]:
    checks = []
    rejection_reasons = []

    source_schema_version = str(
        _first_value(
            source_result,
            ("schema_version",),
            "",
        )
    ).strip()

    schema_accepted = (
        source_schema_version == "RGD-002"
    )

    checks.append(
        _make_check(
            check_id=(
                "source_schema_version"
            ),
            accepted=schema_accepted,
            explanation=(
                "Source result uses the "
                "canonical RGD-002 schema."
                if schema_accepted
                else
                "Source result does not use "
                "the canonical RGD-002 schema."
            ),
            details={
                "expected": "RGD-002",
                "actual": (
                    source_schema_version
                ),
            },
        )
    )

    if not schema_accepted:
        rejection_reasons.append(
            "invalid_source_schema_version"
        )

    source_engine_id = str(
        _first_value(
            source_result,
            ("engine_id",),
            "",
        )
    ).strip()

    engine_accepted = (
        source_engine_id
        == (
            "oracle.discovery.market_regime."
            "source_adapter"
        )
    )

    checks.append(
        _make_check(
            check_id="source_engine_id",
            accepted=engine_accepted,
            explanation=(
                "Source result was produced "
                "by the canonical market "
                "regime source adapter."
                if engine_accepted
                else
                "Source result was not "
                "produced by the canonical "
                "market regime source adapter."
            ),
            details={
                "expected": (
                    "oracle.discovery."
                    "market_regime."
                    "source_adapter"
                ),
                "actual": source_engine_id,
            },
        )
    )

    if not engine_accepted:
        rejection_reasons.append(
            "invalid_source_engine_id"
        )

    source_status = str(
        _first_value(
            source_result,
            ("status",),
            "",
        )
    ).strip().lower()

    status_accepted = (
        source_status
        in ACCEPTED_SOURCE_STATUSES
    )

    checks.append(
        _make_check(
            check_id="source_status",
            accepted=status_accepted,
            explanation=(
                "Source status is accepted "
                "for discovery processing."
                if status_accepted
                else
                "Source status is not accepted "
                "for discovery processing."
            ),
            details={
                "accepted_statuses": tuple(
                    sorted(
                        ACCEPTED_SOURCE_STATUSES
                    )
                ),
                "actual": source_status,
            },
        )
    )

    if not status_accepted:
        rejection_reasons.append(
            "invalid_source_status"
        )

    source_read_only = _first_value(
        source_result,
        ("read_only",),
        None,
    )

    read_only_accepted = (
        source_read_only is True
    )

    checks.append(
        _make_check(
            check_id="source_read_only",
            accepted=read_only_accepted,
            explanation=(
                "Source result is explicitly "
                "read-only."
                if read_only_accepted
                else
                "Source result is not "
                "explicitly read-only."
            ),
            details={
                "actual": source_read_only,
            },
        )
    )

    if not read_only_accepted:
        rejection_reasons.append(
            "source_not_read_only"
        )

    records = _extract_records(
        source_result
    )

    record_ids = [
        _extract_record_id(
            record,
            index,
        )
        for index, record
        in enumerate(records)
    ]

    identifiers_unique = (
        len(record_ids)
        == len(set(record_ids))
    )

    checks.append(
        _make_check(
            check_id=(
                "source_record_identifiers"
            ),
            accepted=identifiers_unique,
            explanation=(
                "Source record identifiers "
                "are unique."
                if identifiers_unique
                else
                "Source record identifiers "
                "contain duplicates."
            ),
            details={
                "record_count": len(records),
                "identifier_count": len(
                    set(record_ids)
                ),
            },
        )
    )

    if not identifiers_unique:
        rejection_reasons.append(
            "duplicate_source_record_id"
        )

    empty_consistency = not (
        source_status == "empty"
        and len(records) != 0
    )

    checks.append(
        _make_check(
            check_id=(
                "source_empty_consistency"
            ),
            accepted=empty_consistency,
            explanation=(
                "Source status and record "
                "count are consistent."
                if empty_consistency
                else
                "Source status is empty but "
                "source records are present."
            ),
            details={
                "status": source_status,
                "record_count": len(records),
            },
        )
    )

    if not empty_consistency:
        rejection_reasons.append(
            "inconsistent_empty_source"
        )

    return (
        tuple(checks),
        tuple(
            sorted(
                set(rejection_reasons)
            )
        ),
    )


def _validate_discovery_result(
    result: MarketRegimeDiscoveryResult,
) -> Tuple[
    Tuple[
        MarketRegimePipelineGateCheck,
        ...,
    ],
    Tuple[str, ...],
]:
    checks = []
    rejection_reasons = []

    type_accepted = isinstance(
        result,
        MarketRegimeDiscoveryResult,
    )

    checks.append(
        _make_check(
            check_id=(
                "discovery_result_type"
            ),
            accepted=type_accepted,
            explanation=(
                "Discovery result uses the "
                "canonical RGD-001 result type."
                if type_accepted
                else
                "Discovery result does not use "
                "the canonical RGD-001 result "
                "type."
            ),
            details={
                "actual_type": type(
                    result
                ).__name__,
            },
        )
    )

    if not type_accepted:
        rejection_reasons.append(
            "invalid_discovery_result_type"
        )

        return (
            tuple(checks),
            tuple(rejection_reasons),
        )

    validation = (
        validate_market_regime_discovery_result(
            result
        )
    )

    contract_accepted = (
        validation.get(
            "accepted",
            False,
        )
        is True
    )

    checks.append(
        _make_check(
            check_id=(
                "discovery_contract"
            ),
            accepted=contract_accepted,
            explanation=(
                "Discovery result satisfies "
                "the canonical RGD-001 "
                "contract."
                if contract_accepted
                else
                "Discovery result failed the "
                "canonical RGD-001 contract."
            ),
            details={
                "contract_checks": (
                    validation.get(
                        "checks",
                        {},
                    )
                ),
            },
        )
    )

    if not contract_accepted:
        rejection_reasons.append(
            "discovery_contract_rejected"
        )

    engine_accepted = (
        result.engine_id
        == (
            "oracle.discovery.market_regime."
            "discovery_engine"
        )
    )

    checks.append(
        _make_check(
            check_id=(
                "discovery_engine_id"
            ),
            accepted=engine_accepted,
            explanation=(
                "Discovery result was produced "
                "by the canonical RGD-003 "
                "engine."
                if engine_accepted
                else
                "Discovery result was not "
                "produced by the canonical "
                "RGD-003 engine."
            ),
            details={
                "actual": result.engine_id,
            },
        )
    )

    if not engine_accepted:
        rejection_reasons.append(
            "invalid_discovery_engine_id"
        )

    status_accepted = (
        result.status
        in ACCEPTED_DISCOVERY_STATUSES
    )

    checks.append(
        _make_check(
            check_id="discovery_status",
            accepted=status_accepted,
            explanation=(
                "Discovery status is accepted "
                "by the pipeline gate."
                if status_accepted
                else
                "Discovery status is not "
                "accepted by the pipeline gate."
            ),
            details={
                "actual": result.status,
                "accepted_statuses": tuple(
                    sorted(
                        ACCEPTED_DISCOVERY_STATUSES
                    )
                ),
            },
        )
    )

    if not status_accepted:
        rejection_reasons.append(
            "invalid_discovery_status"
        )

    read_only_accepted = (
        result.read_only is True
    )

    checks.append(
        _make_check(
            check_id=(
                "discovery_read_only"
            ),
            accepted=read_only_accepted,
            explanation=(
                "Discovery result is "
                "read-only."
                if read_only_accepted
                else
                "Discovery result is not "
                "read-only."
            ),
            details={
                "actual": result.read_only,
            },
        )
    )

    if not read_only_accepted:
        rejection_reasons.append(
            "discovery_not_read_only"
        )

    hash_accepted = (
        result.verify_result_hash() is True
    )

    checks.append(
        _make_check(
            check_id=(
                "discovery_result_hash"
            ),
            accepted=hash_accepted,
            explanation=(
                "Discovery result hash "
                "verified successfully."
                if hash_accepted
                else
                "Discovery result hash did "
                "not verify."
            ),
            details={
                "result_hash": (
                    result.result_hash
                ),
            },
        )
    )

    if not hash_accepted:
        rejection_reasons.append(
            "invalid_discovery_result_hash"
        )

    opportunity_count_accepted = (
        result.opportunity_count
        == len(result.opportunities)
    )

    checks.append(
        _make_check(
            check_id=(
                "discovery_opportunity_count"
            ),
            accepted=(
                opportunity_count_accepted
            ),
            explanation=(
                "Discovery opportunity count "
                "matches the immutable "
                "opportunity collection."
                if opportunity_count_accepted
                else
                "Discovery opportunity count "
                "does not match the "
                "opportunity collection."
            ),
            details={
                "declared_count": (
                    result.opportunity_count
                ),
                "actual_count": len(
                    result.opportunities
                ),
            },
        )
    )

    if not opportunity_count_accepted:
        rejection_reasons.append(
            "invalid_opportunity_count"
        )

    empty_consistency = (
        (
            result.status == "empty"
            and result.opportunity_count == 0
        )
        or (
            result.status == "ok"
            and result.opportunity_count > 0
        )
    )

    checks.append(
        _make_check(
            check_id=(
                "discovery_status_consistency"
            ),
            accepted=empty_consistency,
            explanation=(
                "Discovery status and "
                "opportunity count are "
                "consistent."
                if empty_consistency
                else
                "Discovery status and "
                "opportunity count are "
                "inconsistent."
            ),
            details={
                "status": result.status,
                "opportunity_count": (
                    result.opportunity_count
                ),
            },
        )
    )

    if not empty_consistency:
        rejection_reasons.append(
            "inconsistent_discovery_status"
        )

    return (
        tuple(checks),
        tuple(
            sorted(
                set(rejection_reasons)
            )
        ),
    )


def _build_gate_result(
    source_result: Any,
    discovery_result: MarketRegimeDiscoveryResult,
    observed_at: str,
    checks: Tuple[
        MarketRegimePipelineGateCheck,
        ...,
    ],
    rejection_reasons: Tuple[str, ...],
) -> MarketRegimePipelineGateResult:
    source_schema_version = str(
        _first_value(
            source_result,
            ("schema_version",),
            "unknown",
        )
    )

    source_engine_id = str(
        _first_value(
            source_result,
            ("engine_id",),
            "unknown",
        )
    )

    source_status = str(
        _first_value(
            source_result,
            ("status",),
            "unknown",
        )
    )

    source_records = _extract_records(
        source_result
    )

    accepted = not rejection_reasons

    if not accepted:
        status = "rejected"
    elif discovery_result.status == "empty":
        status = "empty"
    else:
        status = "accepted"

    source_payload = (
        _canonical_source_payload(
            source_result
        )
    )

    source_hash = str(
        _first_value(
            source_result,
            (
                "source_hash",
                "result_hash",
                "adapter_hash",
            ),
            "",
        )
    ).strip()

    if not source_hash:
        source_hash = _stable_hash(
            source_payload
        )

    discovery_hash = str(
        discovery_result.result_hash
    )

    provisional = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "accepted": accepted,
        "observed_at": observed_at,
        "source_schema_version": (
            source_schema_version
        ),
        "source_engine_id": (
            source_engine_id
        ),
        "source_status": source_status,
        "source_record_count": len(
            source_records
        ),
        "discovery_schema_version": (
            discovery_result.schema_version
        ),
        "discovery_engine_id": (
            discovery_result.engine_id
        ),
        "discovery_status": (
            discovery_result.status
        ),
        "opportunity_count": (
            discovery_result
            .opportunity_count
        ),
        "checks": tuple(
            check.as_dict()
            for check in checks
        ),
        "rejection_reasons": (
            rejection_reasons
        ),
        "source_hash": source_hash,
        "discovery_hash": (
            discovery_hash
        ),
        "read_only": True,
    }

    gate_hash = _stable_hash(
        provisional
    )

    return MarketRegimePipelineGateResult(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        status=status,
        accepted=accepted,
        observed_at=observed_at,
        source_schema_version=(
            source_schema_version
        ),
        source_engine_id=source_engine_id,
        source_status=source_status,
        source_record_count=len(
            source_records
        ),
        discovery_schema_version=(
            discovery_result.schema_version
        ),
        discovery_engine_id=(
            discovery_result.engine_id
        ),
        discovery_status=(
            discovery_result.status
        ),
        opportunity_count=(
            discovery_result
            .opportunity_count
        ),
        checks=checks,
        rejection_reasons=(
            rejection_reasons
        ),
        source_hash=source_hash,
        discovery_hash=discovery_hash,
        gate_hash=gate_hash,
        read_only=True,
    )


def evaluate_market_regime_pipeline(
    source_result: Any,
    discovery_result: Optional[
        MarketRegimeDiscoveryResult
    ] = None,
    observed_at: Optional[str] = None,
    config: Optional[
        MarketRegimeEngineConfig
    ] = None,
) -> MarketRegimePipelineGateResult:
    if source_result is None:
        raise TypeError(
            "source_result must not be None"
        )

    resolved_observed_at = (
        _resolve_observed_at(
            source_result=source_result,
            observed_at=observed_at,
        )
    )

    (
        source_checks,
        source_rejections,
    ) = _validate_source_result(
        source_result
    )

    if discovery_result is None:
        discovery_result = (
            discover_market_regimes(
                source_result=source_result,
                observed_at=(
                    resolved_observed_at
                ),
                config=config,
            )
        )

    (
        discovery_checks,
        discovery_rejections,
    ) = _validate_discovery_result(
        discovery_result
    )

    checks = tuple(
        sorted(
            (
                *source_checks,
                *discovery_checks,
            ),
            key=lambda item: item.check_id,
        )
    )

    rejection_reasons = tuple(
        sorted(
            set(
                (
                    *source_rejections,
                    *discovery_rejections,
                )
            )
        )
    )

    result = _build_gate_result(
        source_result=source_result,
        discovery_result=(
            discovery_result
        ),
        observed_at=resolved_observed_at,
        checks=checks,
        rejection_reasons=(
            rejection_reasons
        ),
    )

    if not result.verify_gate_hash():
        raise AssertionError(
            "pipeline gate produced an "
            "invalid deterministic hash"
        )

    return result


def run_market_regime_pipeline_gate(
    source_result: Any,
    discovery_result: Optional[
        MarketRegimeDiscoveryResult
    ] = None,
    observed_at: Optional[str] = None,
    config: Optional[
        MarketRegimeEngineConfig
    ] = None,
) -> MarketRegimePipelineGateResult:
    return evaluate_market_regime_pipeline(
        source_result=source_result,
        discovery_result=(
            discovery_result
        ),
        observed_at=observed_at,
        config=config,
    )


def validate_market_regime_pipeline_gate(
    result: Any,
) -> Dict[str, Any]:
    checks = {
        "result_type": isinstance(
            result,
            MarketRegimePipelineGateResult,
        ),
        "schema_version": (
            getattr(
                result,
                "schema_version",
                None,
            )
            == SCHEMA_VERSION
        ),
        "engine_id": (
            getattr(
                result,
                "engine_id",
                None,
            )
            == ENGINE_ID
        ),
        "status": (
            getattr(
                result,
                "status",
                None,
            )
            in GATE_STATUSES
        ),
        "read_only": (
            getattr(
                result,
                "read_only",
                None,
            )
            is True
        ),
        "hash_valid": (
            isinstance(
                result,
                MarketRegimePipelineGateResult,
            )
            and result.verify_gate_hash()
        ),
    }

    return {
        "accepted": all(
            checks.values()
        ),
        "checks": checks,
    }


def assert_market_regime_pipeline_read_only(
    result: MarketRegimePipelineGateResult,
) -> bool:
    if not isinstance(
        result,
        MarketRegimePipelineGateResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimePipelineGateResult"
        )

    if READ_ONLY is not True:
        raise AssertionError(
            "market regime pipeline gate "
            "must be read-only"
        )

    if result.read_only is not True:
        raise AssertionError(
            "pipeline gate result must be "
            "read-only"
        )

    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ACCEPTED_SOURCE_STATUSES",
    "ACCEPTED_DISCOVERY_STATUSES",
    "GATE_STATUSES",
    "MarketRegimePipelineGateCheck",
    "MarketRegimePipelineGateResult",
    "evaluate_market_regime_pipeline",
    "run_market_regime_pipeline_gate",
    "validate_market_regime_pipeline_gate",
    "assert_market_regime_pipeline_read_only",
]
