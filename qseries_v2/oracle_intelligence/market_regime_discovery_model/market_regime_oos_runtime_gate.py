
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .market_regime_pipeline_bridge import (
    MarketRegimePipelineBridgeResult,
    run_market_regime_pipeline,
    validate_market_regime_pipeline_bridge,
)


READ_ONLY = True
SCHEMA_VERSION = "RGD-007"

ENGINE_ID = (
    "oracle.discovery.market_regime."
    "oos_runtime_gate"
)

OOS_STATUSES = frozenset(
    {
        "accepted",
        "empty",
        "rejected",
    }
)


def _stable_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _stable_value(value[key])
            for key in sorted(value.keys(), key=str)
        }

    if isinstance(value, tuple):
        return tuple(_stable_value(item) for item in value)

    if isinstance(value, list):
        return tuple(_stable_value(item) for item in value)

    if isinstance(value, set):
        return tuple(
            sorted(
                (_stable_value(item) for item in value),
                key=repr,
            )
        )

    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _stable_value(value.as_dict())

    if is_dataclass(value):
        return _stable_value(asdict(value))

    return value


def _stable_hash(value: Any) -> str:
    return sha256(
        repr(_stable_value(value)).encode("utf-8")
    ).hexdigest()


def _artifact_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if hasattr(value, "as_dict") and callable(value.as_dict):
        result = value.as_dict()
        if not isinstance(result, Mapping):
            raise TypeError(
                "as_dict() must return a mapping"
            )
        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                result.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if is_dataclass(value):
        result = asdict(value)
        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                result.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    raise TypeError(
        "artifact must be a mapping, dataclass, "
        "or expose as_dict()"
    )


def _read_value(
    value: Any,
    key: str,
    default: Any = None,
) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _first_value(
    value: Any,
    keys: Sequence[str],
    default: Any = None,
) -> Any:
    for key in keys:
        result = _read_value(value, key, None)
        if result is not None:
            return result
    return default


def _parse_timestamp(value: str) -> datetime:
    normalized = str(value).strip()

    if not normalized:
        raise ValueError(
            "timestamp must not be empty"
        )

    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _normalize_metadata(
    metadata: Optional[Mapping[str, Any]],
) -> Tuple[Tuple[str, Any], ...]:
    if metadata is None:
        return tuple()

    if not isinstance(metadata, Mapping):
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
            key=lambda item: str(item[0]),
        )
    )


def _metadata_dict(
    metadata: Tuple[Tuple[str, Any], ...],
) -> Dict[str, Any]:
    return {
        str(key): _stable_value(value)
        for key, value in metadata
    }


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


def _record_timestamp(record: Any) -> str:
    return str(
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


@dataclass(frozen=True)
class MarketRegimeOOSWindow:
    training_end: str
    evaluation_start: str
    evaluation_end: str

    def __post_init__(self) -> None:
        training_end = _parse_timestamp(
            self.training_end
        )
        evaluation_start = _parse_timestamp(
            self.evaluation_start
        )
        evaluation_end = _parse_timestamp(
            self.evaluation_end
        )

        if training_end >= evaluation_start:
            raise ValueError(
                "training_end must be before "
                "evaluation_start"
            )

        if evaluation_start > evaluation_end:
            raise ValueError(
                "evaluation_start must not be "
                "after evaluation_end"
            )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "training_end": self.training_end,
            "evaluation_start": (
                self.evaluation_start
            ),
            "evaluation_end": (
                self.evaluation_end
            ),
        }


@dataclass(frozen=True)
class MarketRegimeOOSCheck:
    check_id: str
    accepted: bool
    explanation: str
    details: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not str(self.check_id).strip():
            raise ValueError(
                "check_id must not be empty"
            )

        if not str(self.explanation).strip():
            raise ValueError(
                "explanation must not be empty"
            )

        object.__setattr__(
            self,
            "details",
            tuple(
                sorted(
                    (
                        (
                            str(key),
                            _stable_value(value),
                        )
                        for key, value in self.details
                    ),
                    key=lambda item: item[0],
                )
            ),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "accepted": self.accepted,
            "explanation": self.explanation,
            "details": {
                key: _stable_value(value)
                for key, value in self.details
            },
        }


@dataclass(frozen=True)
class MarketRegimeOOSRuntimeGateResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    observed_at: str
    window: MarketRegimeOOSWindow
    pipeline_result: MarketRegimePipelineBridgeResult
    source_record_count: int
    in_window_record_count: int
    pre_window_record_count: int
    post_window_record_count: int
    invalid_timestamp_record_count: int
    checks: Tuple[
        MarketRegimeOOSCheck,
        ...,
    ]
    rejection_reasons: Tuple[str, ...]
    metadata: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(default_factory=tuple)
    result_hash: str = ""
    read_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                "invalid OOS schema_version"
            )

        if self.engine_id != ENGINE_ID:
            raise ValueError(
                "invalid OOS engine_id"
            )

        if self.status not in OOS_STATUSES:
            raise ValueError(
                "invalid OOS status"
            )

        if not str(self.observed_at).strip():
            raise ValueError(
                "observed_at must not be empty"
            )

        counts = (
            self.source_record_count,
            self.in_window_record_count,
            self.pre_window_record_count,
            self.post_window_record_count,
            self.invalid_timestamp_record_count,
        )

        if any(count < 0 for count in counts):
            raise ValueError(
                "record counts cannot be negative"
            )

        if (
            self.in_window_record_count
            + self.pre_window_record_count
            + self.post_window_record_count
            + self.invalid_timestamp_record_count
            != self.source_record_count
        ):
            raise ValueError(
                "record partitions do not match "
                "source_record_count"
            )

        if self.read_only is not True:
            raise ValueError(
                "OOS runtime gate must be "
                "read-only"
            )

        if not isinstance(
            self.pipeline_result,
            MarketRegimePipelineBridgeResult,
        ):
            raise TypeError(
                "pipeline_result must be a "
                "MarketRegimePipelineBridgeResult"
            )

        check_ids = [
            check.check_id
            for check in self.checks
        ]

        if len(check_ids) != len(set(check_ids)):
            raise ValueError(
                "OOS check identifiers must "
                "be unique"
            )

        if self.accepted:
            if self.status not in {
                "accepted",
                "empty",
            }:
                raise ValueError(
                    "accepted OOS gate must have "
                    "accepted or empty status"
                )

            if self.rejection_reasons:
                raise ValueError(
                    "accepted OOS gate cannot "
                    "contain rejection reasons"
                )

            if not all(
                check.accepted
                for check in self.checks
            ):
                raise ValueError(
                    "accepted OOS gate requires "
                    "all checks accepted"
                )
        else:
            if self.status != "rejected":
                raise ValueError(
                    "rejected OOS gate must have "
                    "rejected status"
                )

            if not self.rejection_reasons:
                raise ValueError(
                    "rejected OOS gate must "
                    "contain rejection reasons"
                )

        if not str(self.result_hash).strip():
            raise ValueError(
                "result_hash must not be empty"
            )

        object.__setattr__(
            self,
            "metadata",
            tuple(
                sorted(
                    (
                        (
                            str(key),
                            _stable_value(value),
                        )
                        for key, value
                        in self.metadata
                    ),
                    key=lambda item: item[0],
                )
            ),
        )

    def payload(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "status": self.status,
            "accepted": self.accepted,
            "observed_at": self.observed_at,
            "window": self.window.as_dict(),
            "pipeline_result": _artifact_dict(
                self.pipeline_result
            ),
            "source_record_count": (
                self.source_record_count
            ),
            "in_window_record_count": (
                self.in_window_record_count
            ),
            "pre_window_record_count": (
                self.pre_window_record_count
            ),
            "post_window_record_count": (
                self.post_window_record_count
            ),
            "invalid_timestamp_record_count": (
                self.invalid_timestamp_record_count
            ),
            "checks": tuple(
                check.as_dict()
                for check in self.checks
            ),
            "rejection_reasons": (
                self.rejection_reasons
            ),
            "metadata": _metadata_dict(
                self.metadata
            ),
            "read_only": self.read_only,
        }

    def as_dict(self) -> Dict[str, Any]:
        payload = self.payload()
        payload["result_hash"] = self.result_hash
        return payload

    def verify_result_hash(self) -> bool:
        return self.result_hash == _stable_hash(
            self.payload()
        )


def _make_check(
    check_id: str,
    accepted: bool,
    explanation: str,
    details: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeOOSCheck:
    return MarketRegimeOOSCheck(
        check_id=check_id,
        accepted=bool(accepted),
        explanation=explanation,
        details=_normalize_metadata(
            details or {}
        ),
    )


def _partition_records(
    source_result: Any,
    window: MarketRegimeOOSWindow,
) -> Tuple[
    Tuple[Any, ...],
    Tuple[Any, ...],
    Tuple[Any, ...],
    Tuple[str, ...],
]:
    records = _extract_records(source_result)

    training_end = _parse_timestamp(
        window.training_end
    )
    evaluation_start = _parse_timestamp(
        window.evaluation_start
    )
    evaluation_end = _parse_timestamp(
        window.evaluation_end
    )

    pre_window = []
    in_window = []
    post_window = []
    invalid_timestamp_ids = []

    for index, record in enumerate(records):
        timestamp_text = _record_timestamp(record)

        record_id = str(
            _first_value(
                record,
                (
                    "signal_id",
                    "record_id",
                    "source_id",
                    "id",
                ),
                f"record-index-{index}",
            )
        )

        try:
            timestamp = _parse_timestamp(
                timestamp_text
            )
        except Exception:
            invalid_timestamp_ids.append(
                record_id
            )
            continue

        if timestamp <= training_end:
            pre_window.append(record)
        elif (
            evaluation_start
            <= timestamp
            <= evaluation_end
        ):
            in_window.append(record)
        else:
            post_window.append(record)

    return (
        tuple(pre_window),
        tuple(in_window),
        tuple(post_window),
        tuple(sorted(invalid_timestamp_ids)),
    )


def evaluate_market_regime_oos_runtime(
    source_result: Any,
    window: MarketRegimeOOSWindow,
    observed_at: Optional[str] = None,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeOOSRuntimeGateResult:
    if source_result is None:
        raise TypeError(
            "source_result must not be None"
        )

    if not isinstance(
        window,
        MarketRegimeOOSWindow,
    ):
        raise TypeError(
            "window must be a "
            "MarketRegimeOOSWindow"
        )

    resolved_observed_at = str(
        observed_at
        if observed_at is not None
        else window.evaluation_end
    ).strip()

    if not resolved_observed_at:
        raise ValueError(
            "observed_at must not be empty"
        )

    (
        pre_window_records,
        in_window_records,
        post_window_records,
        invalid_timestamp_ids,
    ) = _partition_records(
        source_result=source_result,
        window=window,
    )

    source_records = _extract_records(
        source_result
    )

    filtered_source = dict(
        _artifact_dict(source_result)
    )

    filtered_source["records"] = (
        in_window_records
    )

    filtered_source["status"] = (
        "ok"
        if in_window_records
        else "empty"
    )

    filtered_source["observed_at"] = (
        resolved_observed_at
    )

    filtered_source["read_only"] = True

    pipeline_result = (
        run_market_regime_pipeline(
            source_result=filtered_source,
            observed_at=resolved_observed_at,
            metadata={
                "oos_runtime_gate_schema": (
                    SCHEMA_VERSION
                ),
                "oos_window": window.as_dict(),
            },
        )
    )

    pipeline_validation = (
        validate_market_regime_pipeline_bridge(
            pipeline_result
        )
    )

    checks = []
    rejection_reasons = []

    timestamps_valid = not invalid_timestamp_ids

    checks.append(
        _make_check(
            check_id="record_timestamps_valid",
            accepted=timestamps_valid,
            explanation=(
                "All source record timestamps "
                "are valid."
                if timestamps_valid
                else
                "One or more source records "
                "have invalid timestamps."
            ),
            details={
                "invalid_record_ids": (
                    invalid_timestamp_ids
                ),
            },
        )
    )

    if not timestamps_valid:
        rejection_reasons.append(
            "invalid_record_timestamp"
        )

    no_training_leakage = (
        len(pre_window_records) == 0
    )

    checks.append(
        _make_check(
            check_id="no_training_leakage",
            accepted=no_training_leakage,
            explanation=(
                "No training-period records "
                "entered the OOS evaluation."
                if no_training_leakage
                else
                "Training-period records were "
                "present in the source input."
            ),
            details={
                "training_record_count": (
                    len(pre_window_records)
                ),
                "training_end": (
                    window.training_end
                ),
            },
        )
    )

    if not no_training_leakage:
        rejection_reasons.append(
            "training_data_leakage"
        )

    no_future_leakage = (
        len(post_window_records) == 0
    )

    checks.append(
        _make_check(
            check_id="no_future_leakage",
            accepted=no_future_leakage,
            explanation=(
                "No post-evaluation records "
                "entered the OOS evaluation."
                if no_future_leakage
                else
                "Post-evaluation records were "
                "present in the source input."
            ),
            details={
                "post_window_record_count": (
                    len(post_window_records)
                ),
                "evaluation_end": (
                    window.evaluation_end
                ),
            },
        )
    )

    if not no_future_leakage:
        rejection_reasons.append(
            "future_data_leakage"
        )

    observed_at_valid = (
        _parse_timestamp(resolved_observed_at)
        <= _parse_timestamp(
            window.evaluation_end
        )
    )

    checks.append(
        _make_check(
            check_id="observed_at_within_window",
            accepted=observed_at_valid,
            explanation=(
                "Runtime observation time does "
                "not exceed evaluation_end."
                if observed_at_valid
                else
                "Runtime observation time "
                "exceeds evaluation_end."
            ),
            details={
                "observed_at": (
                    resolved_observed_at
                ),
                "evaluation_end": (
                    window.evaluation_end
                ),
            },
        )
    )

    if not observed_at_valid:
        rejection_reasons.append(
            "runtime_after_evaluation_end"
        )

    pipeline_valid = (
        pipeline_validation["accepted"]
        is True
    )

    checks.append(
        _make_check(
            check_id="pipeline_valid",
            accepted=pipeline_valid,
            explanation=(
                "RGD-006 pipeline validation "
                "passed."
                if pipeline_valid
                else
                "RGD-006 pipeline validation "
                "failed."
            ),
            details={
                "pipeline_status": (
                    pipeline_result.status
                ),
                "pipeline_accepted": (
                    pipeline_result.accepted
                ),
            },
        )
    )

    if not pipeline_valid:
        rejection_reasons.append(
            "invalid_pipeline_result"
        )

    pipeline_accepted = (
        pipeline_result.accepted is True
    )

    checks.append(
        _make_check(
            check_id="pipeline_accepted",
            accepted=pipeline_accepted,
            explanation=(
                "RGD-006 pipeline accepted the "
                "OOS source projection."
                if pipeline_accepted
                else
                "RGD-006 pipeline rejected the "
                "OOS source projection."
            ),
            details={
                "pipeline_rejections": (
                    pipeline_result
                    .rejection_reasons
                ),
            },
        )
    )

    if not pipeline_accepted:
        rejection_reasons.append(
            "pipeline_rejected"
        )

    read_only_valid = (
        pipeline_result.read_only is True
        and all(
            stage.read_only
            for stage in pipeline_result.stages
        )
    )

    checks.append(
        _make_check(
            check_id="runtime_read_only",
            accepted=read_only_valid,
            explanation=(
                "OOS runtime and all pipeline "
                "stages are read-only."
                if read_only_valid
                else
                "OOS runtime detected a "
                "non-read-only pipeline stage."
            ),
            details={
                "pipeline_read_only": (
                    pipeline_result.read_only
                ),
            },
        )
    )

    if not read_only_valid:
        rejection_reasons.append(
            "runtime_not_read_only"
        )

    checks = tuple(
        sorted(
            checks,
            key=lambda item: item.check_id,
        )
    )

    normalized_rejections = tuple(
        sorted(set(rejection_reasons))
    )

    accepted = not normalized_rejections

    if not accepted:
        status = "rejected"
    elif not in_window_records:
        status = "empty"
    else:
        status = "accepted"

    runtime_metadata = {
        "runtime_mode": (
            "out_of_sample_evaluation"
        ),
        "filtered_source_hash": (
            _stable_hash(filtered_source)
        ),
        "pipeline_hash": (
            pipeline_result.pipeline_hash
        ),
        "external_state_mutated": False,
        "order_placement_performed": False,
        "transaction_signed": False,
        "training_data_consumed": False,
        "future_data_consumed": False,
        "deterministic": True,
        "immutable": True,
        "replayable": True,
        "explainable": True,
        "auditable": True,
        "read_only": True,
    }

    if metadata:
        for key, value in metadata.items():
            runtime_metadata[str(key)] = (
                _stable_value(value)
            )

    normalized_metadata = _normalize_metadata(
        runtime_metadata
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "accepted": accepted,
        "observed_at": resolved_observed_at,
        "window": window.as_dict(),
        "pipeline_result": _artifact_dict(
            pipeline_result
        ),
        "source_record_count": (
            len(source_records)
        ),
        "in_window_record_count": (
            len(in_window_records)
        ),
        "pre_window_record_count": (
            len(pre_window_records)
        ),
        "post_window_record_count": (
            len(post_window_records)
        ),
        "invalid_timestamp_record_count": (
            len(invalid_timestamp_ids)
        ),
        "checks": tuple(
            check.as_dict()
            for check in checks
        ),
        "rejection_reasons": (
            normalized_rejections
        ),
        "metadata": _metadata_dict(
            normalized_metadata
        ),
        "read_only": True,
    }

    result = MarketRegimeOOSRuntimeGateResult(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        status=status,
        accepted=accepted,
        observed_at=resolved_observed_at,
        window=window,
        pipeline_result=pipeline_result,
        source_record_count=len(
            source_records
        ),
        in_window_record_count=len(
            in_window_records
        ),
        pre_window_record_count=len(
            pre_window_records
        ),
        post_window_record_count=len(
            post_window_records
        ),
        invalid_timestamp_record_count=len(
            invalid_timestamp_ids
        ),
        checks=checks,
        rejection_reasons=(
            normalized_rejections
        ),
        metadata=normalized_metadata,
        result_hash=_stable_hash(payload),
        read_only=True,
    )

    if not result.verify_result_hash():
        raise AssertionError(
            "OOS runtime gate produced an "
            "invalid deterministic hash"
        )

    return result


def run_market_regime_oos_runtime_gate(
    source_result: Any,
    window: MarketRegimeOOSWindow,
    observed_at: Optional[str] = None,
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeOOSRuntimeGateResult:
    return evaluate_market_regime_oos_runtime(
        source_result=source_result,
        window=window,
        observed_at=observed_at,
        metadata=metadata,
    )


def validate_market_regime_oos_runtime_gate(
    result: Any,
) -> Dict[str, Any]:
    checks = {
        "result_type": isinstance(
            result,
            MarketRegimeOOSRuntimeGateResult,
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
            in OOS_STATUSES
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
                MarketRegimeOOSRuntimeGateResult,
            )
            and result.verify_result_hash()
        ),
        "pipeline_valid": (
            isinstance(
                result,
                MarketRegimeOOSRuntimeGateResult,
            )
            and (
                validate_market_regime_pipeline_bridge(
                    result.pipeline_result
                )["accepted"]
                is True
            )
        ),
        "partition_counts": (
            isinstance(
                result,
                MarketRegimeOOSRuntimeGateResult,
            )
            and (
                result.in_window_record_count
                + result.pre_window_record_count
                + result.post_window_record_count
                + result.invalid_timestamp_record_count
                == result.source_record_count
            )
        ),
    }

    return {
        "accepted": all(
            checks.values()
        ),
        "checks": checks,
    }


def assert_market_regime_oos_runtime_read_only(
    result: MarketRegimeOOSRuntimeGateResult,
) -> bool:
    if not isinstance(
        result,
        MarketRegimeOOSRuntimeGateResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimeOOSRuntimeGateResult"
        )

    if READ_ONLY is not True:
        raise AssertionError(
            "market regime OOS runtime gate "
            "must be read-only"
        )

    if result.read_only is not True:
        raise AssertionError(
            "OOS runtime result must be "
            "read-only"
        )

    metadata = dict(result.metadata)

    protected_flags = {
        "external_state_mutated": False,
        "order_placement_performed": False,
        "transaction_signed": False,
        "training_data_consumed": False,
        "future_data_consumed": False,
        "read_only": True,
    }

    for key, expected in protected_flags.items():
        if metadata.get(key) is not expected:
            raise AssertionError(
                f"invalid read-only flag: {key}"
            )

    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OOS_STATUSES",
    "MarketRegimeOOSWindow",
    "MarketRegimeOOSCheck",
    "MarketRegimeOOSRuntimeGateResult",
    "evaluate_market_regime_oos_runtime",
    "run_market_regime_oos_runtime_gate",
    "validate_market_regime_oos_runtime_gate",
    "assert_market_regime_oos_runtime_read_only",
]
