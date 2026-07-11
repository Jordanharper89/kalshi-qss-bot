from pathlib import Path


ROOT = Path.cwd()
INTEGRATION_DIR = ROOT / "qseries_v2" / "integration"

MODULE_PATH = (
    INTEGRATION_DIR
    / "qseries_final_execution_authorization_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_int_015_qseries_final_execution_authorization_gate.py"
)

INIT_PATH = INTEGRATION_DIR / "__init__.py"


MODULE_CODE = r'''
"""
INT-015 — Q Series Final Execution Authorization Gate.

Consumes an INT-014 execution-readiness result and creates immutable
authorization decisions for a later execution adapter.

This module does not place orders, call exchanges, move funds, or mutate
portfolio state.
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
    is_dataclass,
)
from enum import Enum
import hashlib
import json
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)


SCHEMA_VERSION = "INT-015"
ENGINE_ID = "INT-015"

SOURCE_SCHEMA_VERSION = "INT-014"
SOURCE_ENGINE_ID = "INT-014"

READ_ONLY = True
EXECUTION_ALLOWED = False
ADAPTER_EXECUTION_REQUIRED = True
QSERIES_OWNED = True


class FinalExecutionAuthorizationStatus(
    str,
    Enum,
):
    AUTHORIZED = "authorized"
    BLOCKED = "blocked"


def _stable_value(
    value: Any,
) -> Any:
    if isinstance(
        value,
        Enum,
    ):
        return _stable_value(
            value.value
        )

    if is_dataclass(
        value
    ):
        return _stable_value(
            asdict(value)
        )

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        }

    if isinstance(
        value,
        (
            tuple,
            list,
        ),
    ):
        return [
            _stable_value(item)
            for item in value
        ]

    if isinstance(
        value,
        set,
    ):
        normalized = [
            _stable_value(item)
            for item in value
        ]

        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    if (
        value is None
        or isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        )
    ):
        return value

    if (
        hasattr(
            value,
            "as_dict",
        )
        and callable(
            value.as_dict
        )
    ):
        return _stable_value(
            value.as_dict()
        )

    if (
        hasattr(
            value,
            "to_dict",
        )
        and callable(
            value.to_dict
        )
    ):
        return _stable_value(
            value.to_dict()
        )

    raise TypeError(
        "value cannot be serialized "
        "canonically"
    )


def _stable_hash(
    value: Any,
) -> str:
    encoded = json.dumps(
        _stable_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _read(
    value: Any,
    key: str,
    default: Any = None,
) -> Any:
    if isinstance(
        value,
        Mapping,
    ):
        return value.get(
            key,
            default,
        )

    return getattr(
        value,
        key,
        default,
    )


def _first(
    value: Any,
    keys: Sequence[str],
    default: Any = None,
) -> Any:
    for key in keys:
        result = _read(
            value,
            key,
            None,
        )

        if result is not None:
            return result

    return default


def _extract_ready_records(
    result: Any,
) -> Tuple[Any, ...]:
    records = _first(
        result,
        (
            "ready_records",
            "ready",
            "records",
            "readiness_records",
            "approved_records",
        ),
        tuple(),
    )

    if records is None:
        return tuple()

    return tuple(
        records
    )


def _normalize_metadata(
    metadata: Optional[
        Mapping[str, Any]
    ],
) -> Tuple[
    Tuple[str, Any],
    ...,
]:
    if metadata is None:
        return tuple()

    if not isinstance(
        metadata,
        Mapping,
    ):
        raise TypeError(
            "metadata must be a mapping"
        )

    return tuple(
        (
            str(key),
            _stable_value(value),
        )
        for key, value in sorted(
            metadata.items(),
            key=lambda item: str(
                item[0]
            ),
        )
    )


def _metadata_dict(
    metadata: Tuple[
        Tuple[str, Any],
        ...,
    ],
) -> Dict[str, Any]:
    return {
        key: _stable_value(value)
        for key, value in metadata
    }


@dataclass(frozen=True)
class FinalExecutionAuthorizationCheck:
    check_id: str
    passed: bool
    explanation: str
    details: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )

    def __post_init__(
        self,
    ) -> None:
        if not str(
            self.check_id
        ).strip():
            raise ValueError(
                "check_id must not be empty"
            )

        if not str(
            self.explanation
        ).strip():
            raise ValueError(
                "explanation must not be empty"
            )

        object.__setattr__(
            self,
            "details",
            tuple(
                sorted(
                    self.details,
                    key=lambda item: item[0],
                )
            ),
        )

    def as_dict(
        self,
    ) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "explanation": (
                self.explanation
            ),
            "details": _metadata_dict(
                self.details
            ),
        }


@dataclass(frozen=True)
class FinalExecutionAuthorizationDecision:
    authorization_id: str
    source_readiness_id: str
    opportunity_id: str
    status: (
        FinalExecutionAuthorizationStatus
    )
    explanation: str
    source_record_hash: str
    semantic_hash: str
    authorized_at: str
    read_only: bool = True
    execution_allowed: bool = False
    adapter_execution_required: bool = True
    qseries_owned: bool = True

    def __post_init__(
        self,
    ) -> None:
        required = {
            "authorization_id": (
                self.authorization_id
            ),
            "source_readiness_id": (
                self.source_readiness_id
            ),
            "opportunity_id": (
                self.opportunity_id
            ),
            "source_record_hash": (
                self.source_record_hash
            ),
            "semantic_hash": (
                self.semantic_hash
            ),
            "authorized_at": (
                self.authorized_at
            ),
        }

        for field_name, value in (
            required.items()
        ):
            if not str(
                value
            ).strip():
                raise ValueError(
                    f"{field_name} must not "
                    "be empty"
                )

        if self.read_only is not True:
            raise ValueError(
                "decision must be read-only"
            )

        if (
            self.execution_allowed
            is not False
        ):
            raise ValueError(
                "INT-015 cannot execute"
            )

        if (
            self.adapter_execution_required
            is not True
        ):
            raise ValueError(
                "execution adapter is required"
            )

        if self.qseries_owned is not True:
            raise ValueError(
                "decision must be Q Series-owned"
            )

    def as_dict(
        self,
    ) -> Dict[str, Any]:
        return {
            "authorization_id": (
                self.authorization_id
            ),
            "source_readiness_id": (
                self.source_readiness_id
            ),
            "opportunity_id": (
                self.opportunity_id
            ),
            "status": self.status.value,
            "explanation": (
                self.explanation
            ),
            "source_record_hash": (
                self.source_record_hash
            ),
            "semantic_hash": (
                self.semantic_hash
            ),
            "authorized_at": (
                self.authorized_at
            ),
            "read_only": self.read_only,
            "execution_allowed": (
                self.execution_allowed
            ),
            "adapter_execution_required": (
                self.adapter_execution_required
            ),
            "qseries_owned": (
                self.qseries_owned
            ),
        }


@dataclass(frozen=True)
class QSeriesFinalExecutionAuthorizationResult:
    schema_version: str
    engine_id: str
    status: str
    authorized_at: str
    source_schema_version: str
    source_engine_id: str
    source_result_hash: str
    decisions: Tuple[
        FinalExecutionAuthorizationDecision,
        ...,
    ]
    checks: Tuple[
        FinalExecutionAuthorizationCheck,
        ...,
    ]
    rejection_reasons: Tuple[
        str,
        ...,
    ]
    telemetry: Tuple[
        Tuple[str, Any],
        ...,
    ]
    result_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    adapter_execution_required: bool = True
    qseries_owned: bool = True

    def __post_init__(
        self,
    ) -> None:
        if (
            self.schema_version
            != SCHEMA_VERSION
        ):
            raise ValueError(
                "invalid schema_version"
            )

        if (
            self.engine_id
            != ENGINE_ID
        ):
            raise ValueError(
                "invalid engine_id"
            )

        if self.status not in {
            "passed",
            "failed",
        }:
            raise ValueError(
                "invalid status"
            )

        if not str(
            self.authorized_at
        ).strip():
            raise ValueError(
                "authorized_at must not be empty"
            )

        if self.read_only is not True:
            raise ValueError(
                "result must be read-only"
            )

        if (
            self.execution_allowed
            is not False
        ):
            raise ValueError(
                "INT-015 cannot execute"
            )

        if (
            self.adapter_execution_required
            is not True
        ):
            raise ValueError(
                "execution adapter is required"
            )

        if self.qseries_owned is not True:
            raise ValueError(
                "result must be Q Series-owned"
            )

        if not str(
            self.result_hash
        ).strip():
            raise ValueError(
                "result_hash must not be empty"
            )

        if self.status == "passed":
            if self.rejection_reasons:
                raise ValueError(
                    "passed result cannot have "
                    "rejection reasons"
                )

            if not self.decisions:
                raise ValueError(
                    "passed result requires "
                    "decisions"
                )

            if not all(
                decision.status
                is FinalExecutionAuthorizationStatus.AUTHORIZED
                for decision in self.decisions
            ):
                raise ValueError(
                    "passed result requires "
                    "authorized decisions"
                )

        if (
            self.status == "failed"
            and not self.rejection_reasons
        ):
            raise ValueError(
                "failed result requires "
                "rejection reasons"
            )

    @property
    def authorized_count(
        self,
    ) -> int:
        return sum(
            decision.status
            is FinalExecutionAuthorizationStatus.AUTHORIZED
            for decision in self.decisions
        )

    @property
    def blocked_count(
        self,
    ) -> int:
        return sum(
            decision.status
            is FinalExecutionAuthorizationStatus.BLOCKED
            for decision in self.decisions
        )

    def payload(
        self,
    ) -> Dict[str, Any]:
        return {
            "schema_version": (
                self.schema_version
            ),
            "engine_id": self.engine_id,
            "status": self.status,
            "authorized_at": (
                self.authorized_at
            ),
            "source_schema_version": (
                self.source_schema_version
            ),
            "source_engine_id": (
                self.source_engine_id
            ),
            "source_result_hash": (
                self.source_result_hash
            ),
            "decisions": [
                decision.as_dict()
                for decision in self.decisions
            ],
            "checks": [
                check.as_dict()
                for check in self.checks
            ],
            "rejection_reasons": list(
                self.rejection_reasons
            ),
            "telemetry": _metadata_dict(
                self.telemetry
            ),
            "read_only": self.read_only,
            "execution_allowed": (
                self.execution_allowed
            ),
            "adapter_execution_required": (
                self.adapter_execution_required
            ),
            "qseries_owned": (
                self.qseries_owned
            ),
        }

    def as_dict(
        self,
    ) -> Dict[str, Any]:
        result = self.payload()

        result["authorized_count"] = (
            self.authorized_count
        )

        result["blocked_count"] = (
            self.blocked_count
        )

        result["result_hash"] = (
            self.result_hash
        )

        return result

    def verify_result_hash(
        self,
    ) -> bool:
        return (
            self.result_hash
            == _stable_hash(
                self.payload()
            )
        )


def _build_check(
    check_id: str,
    passed: bool,
    explanation: str,
    **details: Any,
) -> FinalExecutionAuthorizationCheck:
    return (
        FinalExecutionAuthorizationCheck(
            check_id=check_id,
            passed=passed,
            explanation=explanation,
            details=_normalize_metadata(
                details
            ),
        )
    )


def authorize_execution_readiness(
    readiness_result: Any,
    *,
    authorized_at: str,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> QSeriesFinalExecutionAuthorizationResult:
    resolved_time = str(
        authorized_at
    ).strip()

    if not resolved_time:
        raise ValueError(
            "authorized_at must not be empty"
        )

    source_schema_version = str(
        _read(
            readiness_result,
            "schema_version",
            "",
        )
    )

    source_engine_id = str(
        _read(
            readiness_result,
            "engine_id",
            "",
        )
    )

    source_status = str(
        _read(
            readiness_result,
            "status",
            "",
        )
    )

    source_read_only = _read(
        readiness_result,
        "read_only",
        None,
    )

    source_execution_allowed = _read(
        readiness_result,
        "execution_allowed",
        None,
    )

    final_gate_required = _first(
        readiness_result,
        (
            "final_execution_gate_required",
            "execution_gate_required",
        ),
        None,
    )

    qseries_owned = _read(
        readiness_result,
        "qseries_owned",
        True,
    )

    ready_records = (
        _extract_ready_records(
            readiness_result
        )
    )

    ready_count = int(
        _read(
            readiness_result,
            "ready_count",
            len(ready_records),
        )
        or 0
    )

    rejected_count = int(
        _first(
            readiness_result,
            (
                "rejected_count",
                "blocked_count",
            ),
            0,
        )
        or 0
    )

    source_payload = (
        readiness_result.as_dict()
        if (
            hasattr(
                readiness_result,
                "as_dict",
            )
            and callable(
                readiness_result.as_dict
            )
        )
        else _stable_value(
            readiness_result
        )
    )

    source_result_hash = str(
        _first(
            readiness_result,
            (
                "result_hash",
                "readiness_hash",
            ),
            _stable_hash(
                source_payload
            ),
        )
    )

    checks = (
        _build_check(
            "source_contract",
            (
                source_schema_version
                == SOURCE_SCHEMA_VERSION
                and source_engine_id
                == SOURCE_ENGINE_ID
            ),
            "Source must be INT-014.",
            schema_version=(
                source_schema_version
            ),
            engine_id=(
                source_engine_id
            ),
        ),
        _build_check(
            "source_passed",
            source_status == "passed",
            "INT-014 must have passed.",
            status=source_status,
        ),
        _build_check(
            "source_read_only",
            source_read_only is True,
            "INT-014 must be read-only.",
            read_only=source_read_only,
        ),
        _build_check(
            "execution_disabled",
            (
                source_execution_allowed
                is False
            ),
            "INT-014 cannot execute.",
            execution_allowed=(
                source_execution_allowed
            ),
        ),
        _build_check(
            "final_gate_required",
            final_gate_required is True,
            "INT-014 must require a final gate.",
            final_execution_gate_required=(
                final_gate_required
            ),
        ),
        _build_check(
            "qseries_owned",
            qseries_owned is True,
            "Result must be Q Series-owned.",
            qseries_owned=qseries_owned,
        ),
        _build_check(
            "ready_records_present",
            (
                ready_count > 0
                and len(
                    ready_records
                ) > 0
            ),
            "At least one ready record is required.",
            ready_count=ready_count,
            record_count=len(
                ready_records
            ),
        ),
        _build_check(
            "no_rejected_records",
            rejected_count == 0,
            "Rejected records cannot cross INT-015.",
            rejected_count=(
                rejected_count
            ),
        ),
    )

    aggregate_passed = all(
        check.passed
        for check in checks
    )

    decisions = []

    if aggregate_passed:
        for index, record in enumerate(
            ready_records
        ):
            record_status = str(
                _first(
                    record,
                    (
                        "status",
                        "readiness_status",
                    ),
                    "",
                )
            ).lower()

            record_owned = _read(
                record,
                "qseries_owned",
                True,
            )

            record_execution_allowed = (
                _read(
                    record,
                    "execution_allowed",
                    False,
                )
            )

            record_gate_required = _first(
                record,
                (
                    "final_execution_gate_required",
                    "execution_gate_required",
                    "adapter_execution_required",
                ),
                True,
            )

            record_valid = (
                record_owned is True
                and (
                    record_execution_allowed
                    is False
                )
                and (
                    record_gate_required
                    is True
                )
                and record_status in {
                    "ready",
                    "ready_for_execution_gate",
                    "passed",
                    "approved",
                    "authorized",
                }
            )

            readiness_id = str(
                _first(
                    record,
                    (
                        "readiness_id",
                        "record_id",
                        "intake_id",
                    ),
                    (
                        "int014_record_"
                        f"{index + 1}"
                    ),
                )
            )

            opportunity_id = str(
                _first(
                    record,
                    (
                        "opportunity_id",
                        "source_opportunity_id",
                    ),
                    readiness_id,
                )
            )

            record_payload = (
                _stable_value(
                    record
                )
            )

            record_hash = str(
                _first(
                    record,
                    (
                        "record_hash",
                        "readiness_hash",
                        "semantic_hash",
                    ),
                    _stable_hash(
                        record_payload
                    ),
                )
            )

            semantic_payload = {
                "source_readiness_id": (
                    readiness_id
                ),
                "opportunity_id": (
                    opportunity_id
                ),
                "source_record_hash": (
                    record_hash
                ),
                "qseries_owned": True,
                "execution_allowed": False,
                "adapter_execution_required": True,
            }

            semantic_hash = (
                _stable_hash(
                    semantic_payload
                )
            )

            authorization_id = (
                "int015_"
                + semantic_hash[:24]
            )

            decisions.append(
                FinalExecutionAuthorizationDecision(
                    authorization_id=(
                        authorization_id
                    ),
                    source_readiness_id=(
                        readiness_id
                    ),
                    opportunity_id=(
                        opportunity_id
                    ),
                    status=(
                        FinalExecutionAuthorizationStatus.AUTHORIZED
                        if record_valid
                        else FinalExecutionAuthorizationStatus.BLOCKED
                    ),
                    explanation=(
                        "Authorized for a later "
                        "execution adapter."
                        if record_valid
                        else
                        "Blocked because the "
                        "readiness record is invalid."
                    ),
                    source_record_hash=(
                        record_hash
                    ),
                    semantic_hash=(
                        semantic_hash
                    ),
                    authorized_at=(
                        resolved_time
                    ),
                )
            )

    rejection_reasons = [
        check.check_id
        for check in checks
        if not check.passed
    ]

    rejection_reasons.extend(
        decision.authorization_id
        for decision in decisions
        if (
            decision.status
            is FinalExecutionAuthorizationStatus.BLOCKED
        )
    )

    status = (
        "passed"
        if (
            decisions
            and not rejection_reasons
        )
        else "failed"
    )

    telemetry_values = {
        "source_ready_count": (
            ready_count
        ),
        "source_rejected_count": (
            rejected_count
        ),
        "decision_count": len(
            decisions
        ),
        "orders_placed": False,
        "exchange_called": False,
        "funds_moved": False,
        "portfolio_mutated": False,
        "files_written": False,
        "database_written": False,
    }

    if metadata:
        telemetry_values["metadata"] = (
            _stable_value(
                metadata
            )
        )

    provisional = (
        QSeriesFinalExecutionAuthorizationResult(
            schema_version=(
                SCHEMA_VERSION
            ),
            engine_id=ENGINE_ID,
            status=status,
            authorized_at=(
                resolved_time
            ),
            source_schema_version=(
                source_schema_version
            ),
            source_engine_id=(
                source_engine_id
            ),
            source_result_hash=(
                source_result_hash
            ),
            decisions=tuple(
                decisions
            ),
            checks=checks,
            rejection_reasons=tuple(
                rejection_reasons
            ),
            telemetry=_normalize_metadata(
                telemetry_values
            ),
            result_hash="pending",
        )
    )

    return (
        QSeriesFinalExecutionAuthorizationResult(
            schema_version=(
                provisional.schema_version
            ),
            engine_id=(
                provisional.engine_id
            ),
            status=(
                provisional.status
            ),
            authorized_at=(
                provisional.authorized_at
            ),
            source_schema_version=(
                provisional.source_schema_version
            ),
            source_engine_id=(
                provisional.source_engine_id
            ),
            source_result_hash=(
                provisional.source_result_hash
            ),
            decisions=(
                provisional.decisions
            ),
            checks=(
                provisional.checks
            ),
            rejection_reasons=(
                provisional.rejection_reasons
            ),
            telemetry=(
                provisional.telemetry
            ),
            result_hash=_stable_hash(
                provisional.payload()
            ),
        )
    )


def validate_qseries_final_execution_authorization_result(
    result: (
        QSeriesFinalExecutionAuthorizationResult
    ),
) -> bool:
    if not isinstance(
        result,
        QSeriesFinalExecutionAuthorizationResult,
    ):
        raise TypeError(
            "result must be a "
            "QSeriesFinalExecutionAuthorizationResult"
        )

    return (
        result.verify_result_hash()
        and result.read_only is True
        and result.execution_allowed is False
        and (
            result.adapter_execution_required
            is True
        )
        and result.qseries_owned is True
    )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "ADAPTER_EXECUTION_REQUIRED",
    "QSERIES_OWNED",
    "FinalExecutionAuthorizationStatus",
    "FinalExecutionAuthorizationCheck",
    "FinalExecutionAuthorizationDecision",
    "QSeriesFinalExecutionAuthorizationResult",
    "authorize_execution_readiness",
    "validate_qseries_final_execution_authorization_result",
]
'''


TEST_CODE = r'''
from dataclasses import (
    FrozenInstanceError,
    dataclass,
)
import json
from pathlib import Path

from qseries_v2.integration.qseries_final_execution_authorization_gate import (
    ADAPTER_EXECUTION_REQUIRED,
    ENGINE_ID,
    EXECUTION_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    FinalExecutionAuthorizationStatus,
    QSeriesFinalExecutionAuthorizationResult,
    authorize_execution_readiness,
    validate_qseries_final_execution_authorization_result,
)


AUTHORIZED_AT = (
    "2026-07-11T00:00:00+00:00"
)


@dataclass(frozen=True)
class FakeReadyRecord:
    readiness_id: str
    opportunity_id: str
    status: str = (
        "ready_for_execution_gate"
    )
    record_hash: str = (
        "record_hash_001"
    )
    qseries_owned: bool = True
    execution_allowed: bool = False
    final_execution_gate_required: (
        bool
    ) = True

    def as_dict(
        self,
    ):
        return {
            "readiness_id": (
                self.readiness_id
            ),
            "opportunity_id": (
                self.opportunity_id
            ),
            "status": self.status,
            "record_hash": (
                self.record_hash
            ),
            "qseries_owned": (
                self.qseries_owned
            ),
            "execution_allowed": (
                self.execution_allowed
            ),
            "final_execution_gate_required": (
                self.final_execution_gate_required
            ),
        }


@dataclass(frozen=True)
class FakeReadinessResult:
    schema_version: str = "INT-014"
    engine_id: str = "INT-014"
    status: str = "passed"
    ready_records: tuple = (
        FakeReadyRecord(
            "int014_ready_001",
            "opp_001",
        ),
        FakeReadyRecord(
            "int014_ready_002",
            "opp_002",
            record_hash=(
                "record_hash_002"
            ),
        ),
    )
    ready_count: int = 2
    rejected_count: int = 0
    result_hash: str = (
        "int014_result_hash"
    )
    read_only: bool = True
    execution_allowed: bool = False
    final_execution_gate_required: (
        bool
    ) = True
    qseries_owned: bool = True

    def as_dict(
        self,
    ):
        return {
            "schema_version": (
                self.schema_version
            ),
            "engine_id": (
                self.engine_id
            ),
            "status": self.status,
            "ready_records": [
                record.as_dict()
                for record
                in self.ready_records
            ],
            "ready_count": (
                self.ready_count
            ),
            "rejected_count": (
                self.rejected_count
            ),
            "result_hash": (
                self.result_hash
            ),
            "read_only": (
                self.read_only
            ),
            "execution_allowed": (
                self.execution_allowed
            ),
            "final_execution_gate_required": (
                self.final_execution_gate_required
            ),
            "qseries_owned": (
                self.qseries_owned
            ),
        }


def test_valid_result():
    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    assert (
        result.schema_version
        == SCHEMA_VERSION
    )

    assert (
        result.engine_id
        == ENGINE_ID
    )

    assert result.status == "passed"

    assert (
        result.authorized_count
        == 2
    )

    assert result.blocked_count == 0

    assert all(
        decision.status
        is FinalExecutionAuthorizationStatus.AUTHORIZED
        for decision in result.decisions
    )

    assert (
        validate_qseries_final_execution_authorization_result(
            result
        )
    )


def test_failed_readiness_result():
    result = authorize_execution_readiness(
        FakeReadinessResult(
            status="failed",
            ready_records=tuple(),
            ready_count=0,
            rejected_count=1,
        ),
        authorized_at=AUTHORIZED_AT,
    )

    assert result.status == "failed"

    assert (
        result.authorized_count
        == 0
    )

    assert result.rejection_reasons


def test_malformed_contract():
    result = authorize_execution_readiness(
        FakeReadinessResult(
            schema_version="INT-999"
        ),
        authorized_at=AUTHORIZED_AT,
    )

    assert result.status == "failed"

    assert (
        "source_contract"
        in result.rejection_reasons
    )


def test_invalid_record_blocked():
    invalid_record = FakeReadyRecord(
        readiness_id="int014_bad",
        opportunity_id="opp_bad",
        status="blocked",
    )

    result = authorize_execution_readiness(
        FakeReadinessResult(
            ready_records=(
                invalid_record,
            ),
            ready_count=1,
        ),
        authorized_at=AUTHORIZED_AT,
    )

    assert result.status == "failed"

    assert result.blocked_count == 1


def test_deterministic_result():
    first = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    second = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    assert first == second

    assert (
        first.result_hash
        == second.result_hash
    )


def test_timestamp_identity():
    first = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=(
            "2026-07-11T00:00:00+00:00"
        ),
    )

    second = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=(
            "2026-07-11T00:01:00+00:00"
        ),
    )

    assert (
        first.result_hash
        != second.result_hash
    )

    assert [
        decision.authorization_id
        for decision in first.decisions
    ] == [
        decision.authorization_id
        for decision in second.decisions
    ]

    assert [
        decision.semantic_hash
        for decision in first.decisions
    ] == [
        decision.semantic_hash
        for decision in second.decisions
    ]


def test_result_frozen():
    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    try:
        result.status = "failed"
        raise AssertionError(
            "result was mutable"
        )
    except FrozenInstanceError:
        pass


def test_json_serialization():
    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    encoded = json.dumps(
        result.as_dict(),
        sort_keys=True,
    )

    decoded = json.loads(
        encoded
    )

    assert (
        decoded["schema_version"]
        == "INT-015"
    )

    assert (
        decoded["authorized_count"]
        == 2
    )


def test_no_side_effects():
    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    telemetry = dict(
        result.telemetry
    )

    assert (
        telemetry["orders_placed"]
        is False
    )

    assert (
        telemetry["exchange_called"]
        is False
    )

    assert (
        telemetry["funds_moved"]
        is False
    )

    assert (
        telemetry["portfolio_mutated"]
        is False
    )

    assert (
        telemetry["files_written"]
        is False
    )

    assert (
        telemetry["database_written"]
        is False
    )

    assert (
        result.read_only
        is READ_ONLY
        is True
    )

    assert (
        result.execution_allowed
        is EXECUTION_ALLOWED
        is False
    )

    assert (
        result.adapter_execution_required
        is ADAPTER_EXECUTION_REQUIRED
        is True
    )


def test_package_export():
    from qseries_v2.integration import (
        QSeriesFinalExecutionAuthorizationResult
        as ExportedResult,
    )

    from qseries_v2.integration import (
        authorize_execution_readiness
        as exported_authorize,
    )

    assert (
        ExportedResult
        is QSeriesFinalExecutionAuthorizationResult
    )

    assert (
        exported_authorize
        is authorize_execution_readiness
    )


def test_installer_idempotence():
    root = Path(
        __file__
    ).resolve().parent

    module_path = (
        root
        / "qseries_v2"
        / "integration"
        / "qseries_final_execution_authorization_gate.py"
    )

    test_path = (
        root
        / "test_int_015_qseries_final_execution_authorization_gate.py"
    )

    init_path = (
        root
        / "qseries_v2"
        / "integration"
        / "__init__.py"
    )

    before = (
        module_path.read_bytes(),
        test_path.read_bytes(),
        init_path.read_bytes(),
    )

    installer_path = (
        root
        / "build_int_015_qseries_final_execution_authorization_gate.py"
    )

    namespace = {
        "__name__": (
            "__installer_test__"
        )
    }

    exec(
        compile(
            installer_path.read_text(
                encoding="utf-8"
            ),
            str(
                installer_path
            ),
            "exec",
        ),
        namespace,
    )

    after = (
        module_path.read_bytes(),
        test_path.read_bytes(),
        init_path.read_bytes(),
    )

    assert before == after


def run_all():
    tests = (
        test_valid_result,
        test_failed_readiness_result,
        test_malformed_contract,
        test_invalid_record_blocked,
        test_deterministic_result,
        test_timestamp_identity,
        test_result_frozen,
        test_json_serialization,
        test_no_side_effects,
        test_package_export,
        test_installer_idempotence,
    )

    for test in tests:
        test()

    result = authorize_execution_readiness(
        FakeReadinessResult(),
        authorized_at=AUTHORIZED_AT,
    )

    print(
        "[PASS] INT-015 "
        "Q Series Final Execution "
        "Authorization Gate"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": (
                result.engine_id
            ),
            "status": (
                result.status
            ),
            "authorized_count": (
                result.authorized_count
            ),
            "blocked_count": (
                result.blocked_count
            ),
            "read_only": (
                result.read_only
            ),
            "execution_allowed": (
                result.execution_allowed
            ),
            "adapter_execution_required": (
                result.adapter_execution_required
            ),
        }
    )


if __name__ == "__main__":
    run_all()
'''


EXPORT_MARKER = (
    "# INT-015 Q Series Final "
    "Execution Authorization Gate"
)


EXPORT_CODE = r'''
# INT-015 Q Series Final Execution Authorization Gate
from .qseries_final_execution_authorization_gate import (
    ADAPTER_EXECUTION_REQUIRED as QSERIES_FINAL_EXECUTION_ADAPTER_REQUIRED,
    ENGINE_ID as QSERIES_FINAL_EXECUTION_AUTHORIZATION_ENGINE_ID,
    EXECUTION_ALLOWED as QSERIES_FINAL_EXECUTION_AUTHORIZATION_EXECUTION_ALLOWED,
    QSERIES_OWNED as QSERIES_FINAL_EXECUTION_AUTHORIZATION_QSERIES_OWNED,
    READ_ONLY as QSERIES_FINAL_EXECUTION_AUTHORIZATION_READ_ONLY,
    SCHEMA_VERSION as QSERIES_FINAL_EXECUTION_AUTHORIZATION_SCHEMA_VERSION,
    FinalExecutionAuthorizationCheck,
    FinalExecutionAuthorizationDecision,
    FinalExecutionAuthorizationStatus,
    QSeriesFinalExecutionAuthorizationResult,
    authorize_execution_readiness,
    validate_qseries_final_execution_authorization_result,
)
'''


def write_if_changed(
    path: Path,
    content: str,
) -> None:
    normalized = (
        content.rstrip()
        + "\n"
    )

    if (
        path.exists()
        and path.read_text(
            encoding="utf-8"
        ) == normalized
    ):
        print(
            f"[OK] Unchanged {path}"
        )
        return

    path.write_text(
        normalized,
        encoding="utf-8",
    )

    print(
        f"[OK] Wrote {path}"
    )


def update_exports() -> None:
    current = (
        INIT_PATH.read_text(
            encoding="utf-8"
        )
        if INIT_PATH.exists()
        else ""
    )

    if EXPORT_MARKER in current:
        print(
            f"[OK] Export already present "
            f"{INIT_PATH}"
        )
        return

    updated = (
        current.rstrip()
        + "\n\n"
        + EXPORT_CODE.strip()
        + "\n"
    )

    INIT_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        f"[OK] Updated {INIT_PATH}"
    )


def main() -> None:
    print(
        "========================================"
    )

    print(
        " INT-015 INSTALLER"
    )

    print(
        " Q Series Final Execution "
        "Authorization Gate"
    )

    print(
        "========================================"
    )

    INTEGRATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_if_changed(
        MODULE_PATH,
        MODULE_CODE,
    )

    write_if_changed(
        TEST_PATH,
        TEST_CODE,
    )

    update_exports()

    print()

    print(
        "[DONE] INT-015 installed"
    )

    print()

    print(
        "Run:"
    )

    print(
        "py "
        "test_int_015_"
        "qseries_final_execution_"
        "authorization_gate.py"
    )


if __name__ == "__main__":
    main()