from pathlib import Path


ROOT = Path.cwd()

PACKAGE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "market_regime_discovery_model"
)

PACKAGE.mkdir(
    parents=True,
    exist_ok=True,
)

MODULE = PACKAGE / "market_regime_pipeline_gate.py"

TEST = ROOT / "test_rgd_004_market_regime_pipeline_gate.py"

INIT = PACKAGE / "__init__.py"


MODULE.write_text(
r'''
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
        source_result.as_dict()
        if hasattr(
            source_result,
            "as_dict",
        )
        and callable(
            source_result.as_dict
        )
        else source_result
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
''',
    encoding="utf-8",
)


TEST.write_text(
r'''
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_discovery_engine import (
    discover_market_regimes,
)

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_pipeline_gate import (
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimePipelineGateCheck,
    MarketRegimePipelineGateResult,
    assert_market_regime_pipeline_read_only,
    evaluate_market_regime_pipeline,
    run_market_regime_pipeline_gate,
    validate_market_regime_pipeline_gate,
)


OBSERVED_AT = "2026-07-09T00:00:00+00:00"


def _record(
    signal_id,
    signal_type,
    value,
    source_family,
    reliability=0.90,
    prior_regime="stable",
):
    return {
        "signal_id": signal_id,
        "market_id": "KXREGIME",
        "venue": "kalshi",
        "asset": "binary_event",
        "source_family": source_family,
        "signal_type": signal_type,
        "value": value,
        "reliability": reliability,
        "observed_at": OBSERVED_AT,
        "prior_regime": prior_regime,
        "source_hash": (
            f"source-hash-{signal_id}"
        ),
        "details": {
            "fixture": True,
        },
    }


def _valid_source():
    return {
        "schema_version": "RGD-002",
        "engine_id": (
            "oracle.discovery.market_regime."
            "source_adapter"
        ),
        "status": "ok",
        "records": (
            _record(
                signal_id="volatility-001",
                signal_type="volatility",
                value=0.95,
                reliability=0.95,
                source_family=(
                    "volatility_discovery"
                ),
            ),
            _record(
                signal_id="dispersion-001",
                signal_type="dispersion",
                value=0.90,
                source_family=(
                    "correlation_discovery"
                ),
            ),
            _record(
                signal_id="correlation-001",
                signal_type=(
                    "correlation_breakdown"
                ),
                value=0.85,
                source_family=(
                    "correlation_discovery"
                ),
            ),
            _record(
                signal_id="liquidity-001",
                signal_type="liquidity",
                value=-0.50,
                reliability=0.85,
                source_family=(
                    "liquidity_discovery"
                ),
            ),
        ),
        "observed_at": OBSERVED_AT,
        "read_only": True,
    }


def _empty_source():
    return {
        "schema_version": "RGD-002",
        "engine_id": (
            "oracle.discovery.market_regime."
            "source_adapter"
        ),
        "status": "empty",
        "records": tuple(),
        "observed_at": OBSERVED_AT,
        "read_only": True,
    }


def test_pipeline_gate_constants():
    assert SCHEMA_VERSION == "RGD-004"
    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "pipeline_gate"
    )
    assert READ_ONLY is True


def test_pipeline_gate_accepts_valid_pipeline():
    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert isinstance(
        result,
        MarketRegimePipelineGateResult,
    )

    assert result.schema_version == "RGD-004"
    assert result.engine_id == ENGINE_ID
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.source_status == "ok"
    assert result.source_record_count == 4
    assert result.discovery_status == "ok"
    assert result.opportunity_count == 1
    assert result.rejection_reasons == tuple()
    assert result.read_only is True
    assert result.verify_gate_hash() is True

    assert all(
        check.accepted
        for check in result.checks
    )


def test_pipeline_gate_accepts_empty_pipeline():
    result = evaluate_market_regime_pipeline(
        source_result=_empty_source(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.source_status == "empty"
    assert result.source_record_count == 0
    assert result.discovery_status == "empty"
    assert result.opportunity_count == 0
    assert result.rejection_reasons == tuple()
    assert result.verify_gate_hash() is True


def test_pipeline_gate_accepts_prebuilt_result():
    source = _valid_source()

    discovery_result = (
        discover_market_regimes(
            source_result=source,
            observed_at=OBSERVED_AT,
        )
    )

    gate_result = (
        evaluate_market_regime_pipeline(
            source_result=source,
            discovery_result=(
                discovery_result
            ),
            observed_at=OBSERVED_AT,
        )
    )

    assert gate_result.accepted is True
    assert gate_result.status == "accepted"

    assert (
        gate_result.discovery_hash
        == discovery_result.result_hash
    )


def test_pipeline_gate_rejects_wrong_source_schema():
    source = dict(
        _valid_source()
    )

    source["schema_version"] = "BAD-001"

    result = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "invalid_source_schema_version"
        in result.rejection_reasons
    )

    check = {
        item.check_id: item
        for item in result.checks
    }["source_schema_version"]

    assert check.accepted is False


def test_pipeline_gate_rejects_wrong_source_engine():
    source = dict(
        _valid_source()
    )

    source["engine_id"] = (
        "oracle.invalid.source"
    )

    result = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "invalid_source_engine_id"
        in result.rejection_reasons
    )


def test_pipeline_gate_rejects_mutable_source():
    source = dict(
        _valid_source()
    )

    source["read_only"] = False

    result = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "source_not_read_only"
        in result.rejection_reasons
    )


def test_pipeline_gate_rejects_duplicate_records():
    source = dict(
        _valid_source()
    )

    record = _record(
        signal_id="duplicate-001",
        signal_type="volatility",
        value=0.90,
        source_family=(
            "volatility_discovery"
        ),
    )

    source["records"] = (
        record,
        record,
    )

    try:
        evaluate_market_regime_pipeline(
            source_result=source,
            observed_at=OBSERVED_AT,
        )
    except ValueError as exc:
        assert str(exc) == (
            "signal identifiers must be unique"
        )
    else:
        raise AssertionError(
            "expected duplicate source "
            "records to be rejected"
        )


def test_pipeline_gate_detects_inconsistent_empty_source():
    source = dict(
        _valid_source()
    )

    source["status"] = "empty"

    result = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert result.accepted is False
    assert result.status == "rejected"

    assert (
        "inconsistent_empty_source"
        in result.rejection_reasons
    )


def test_pipeline_gate_is_deterministic():
    result_1 = run_market_regime_pipeline_gate(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    result_2 = run_market_regime_pipeline_gate(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert result_1 == result_2

    assert (
        result_1.gate_hash
        == result_2.gate_hash
    )

    assert (
        result_1.source_hash
        == result_2.source_hash
    )

    assert (
        result_1.discovery_hash
        == result_2.discovery_hash
    )


def test_pipeline_gate_input_order_independent():
    source = _valid_source()

    reversed_source = dict(source)

    reversed_source["records"] = tuple(
        reversed(
            source["records"]
        )
    )

    result_1 = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    result_2 = evaluate_market_regime_pipeline(
        source_result=reversed_source,
        observed_at=OBSERVED_AT,
    )

    assert (
        result_1.discovery_hash
        == result_2.discovery_hash
    )

    assert (
        result_1.status
        == result_2.status
    )

    assert (
        result_1.opportunity_count
        == result_2.opportunity_count
    )


def test_pipeline_gate_validation():
    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    validation = (
        validate_market_regime_pipeline_gate(
            result
        )
    )

    assert validation["accepted"] is True
    assert all(
        validation["checks"].values()
    )


def test_pipeline_gate_read_only():
    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert (
        assert_market_regime_pipeline_read_only(
            result
        )
        is True
    )

    try:
        result.status = "rejected"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "gate result must be immutable"
        )

    check = result.checks[0]

    assert isinstance(
        check,
        MarketRegimePipelineGateCheck,
    )

    try:
        check.accepted = False
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "gate check must be immutable"
        )


def test_pipeline_gate_as_dict():
    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-004"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["accepted"] is True
    assert payload["read_only"] is True

    assert payload["gate_hash"] == (
        result.gate_hash
    )

    assert len(payload["checks"]) == len(
        result.checks
    )


def test_pipeline_gate_requires_source():
    try:
        evaluate_market_regime_pipeline(
            source_result=None,
            observed_at=OBSERVED_AT,
        )
    except TypeError as exc:
        assert str(exc) == (
            "source_result must not be None"
        )
    else:
        raise AssertionError(
            "expected source requirement"
        )


if __name__ == "__main__":
    test_pipeline_gate_constants()
    test_pipeline_gate_accepts_valid_pipeline()
    test_pipeline_gate_accepts_empty_pipeline()
    test_pipeline_gate_accepts_prebuilt_result()
    test_pipeline_gate_rejects_wrong_source_schema()
    test_pipeline_gate_rejects_wrong_source_engine()
    test_pipeline_gate_rejects_mutable_source()
    test_pipeline_gate_rejects_duplicate_records()
    test_pipeline_gate_detects_inconsistent_empty_source()
    test_pipeline_gate_is_deterministic()
    test_pipeline_gate_input_order_independent()
    test_pipeline_gate_validation()
    test_pipeline_gate_read_only()
    test_pipeline_gate_as_dict()
    test_pipeline_gate_requires_source()

    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-004 "
        "Market Regime Pipeline Gate"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "source_records": (
                result.source_record_count
            ),
            "opportunities": (
                result.opportunity_count
            ),
            "checks": len(
                result.checks
            ),
            "read_only": result.read_only,
        }
    )
''',
    encoding="utf-8",
)


existing_init = (
    INIT.read_text(
        encoding="utf-8"
    )
    if INIT.exists()
    else ""
)

gate_import = r'''
from .market_regime_pipeline_gate import (
    ACCEPTED_DISCOVERY_STATUSES,
    ACCEPTED_SOURCE_STATUSES,
    ENGINE_ID as PIPELINE_GATE_ENGINE_ID,
    GATE_STATUSES,
    READ_ONLY as PIPELINE_GATE_READ_ONLY,
    SCHEMA_VERSION as PIPELINE_GATE_SCHEMA_VERSION,
    MarketRegimePipelineGateCheck,
    MarketRegimePipelineGateResult,
    assert_market_regime_pipeline_read_only,
    evaluate_market_regime_pipeline,
    run_market_regime_pipeline_gate,
    validate_market_regime_pipeline_gate,
)
'''

if (
    "from .market_regime_pipeline_gate import"
    not in existing_init
):
    updated_init = (
        existing_init.rstrip()
        + "\n\n"
        + gate_import.strip()
        + "\n"
    )

    INIT.write_text(
        updated_init,
        encoding="utf-8",
    )


print("========================================")
print(" RGD-004 INSTALLER")
print(" Market Regime Pipeline Gate")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] RGD-004 installed")
print()
print("Run:")
print(
    "py "
    "test_rgd_004_market_regime_"
    "pipeline_gate.py"
)