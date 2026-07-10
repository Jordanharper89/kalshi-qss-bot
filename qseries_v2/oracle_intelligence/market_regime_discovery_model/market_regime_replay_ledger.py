
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .market_regime_oos_runtime_gate import (
    MarketRegimeOOSRuntimeGateResult,
    MarketRegimeOOSWindow,
    evaluate_market_regime_oos_runtime,
    validate_market_regime_oos_runtime_gate,
)


READ_ONLY = True
SCHEMA_VERSION = "RGD-008"

ENGINE_ID = (
    "oracle.discovery.market_regime."
    "replay_ledger"
)

LEDGER_STATUSES = frozenset(
    {
        "recorded",
        "empty",
        "rejected",
    }
)


def _stable_value(value: Any) -> Any:
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

    if is_dataclass(value):
        return _stable_value(
            asdict(value)
        )

    return value


def _stable_hash(value: Any) -> str:
    return sha256(
        repr(
            _stable_value(value)
        ).encode("utf-8")
    ).hexdigest()


def _artifact_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        }

    if hasattr(value, "as_dict") and callable(
        value.as_dict
    ):
        result = value.as_dict()

        if not isinstance(result, Mapping):
            raise TypeError(
                "as_dict() must return a mapping"
            )

        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                result.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        }

    if is_dataclass(value):
        result = asdict(value)

        return {
            str(key): _stable_value(item)
            for key, item in sorted(
                result.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        }

    raise TypeError(
        "artifact must be a mapping, dataclass, "
        "or expose as_dict()"
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
        str(key): _stable_value(value)
        for key, value in metadata
    }


@dataclass(frozen=True)
class MarketRegimeReplayEntry:
    sequence: int
    replay_id: str
    observed_at: str
    source_hash: str
    window_hash: str
    runtime_hash: str
    previous_entry_hash: str
    status: str
    accepted: bool
    source_record_count: int
    in_window_record_count: int
    opportunity_count: int
    pipeline_status: str
    entry_hash: str
    metadata: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )
    read_only: bool = True

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError(
                "sequence must be at least 1"
            )

        required = {
            "replay_id": self.replay_id,
            "observed_at": self.observed_at,
            "source_hash": self.source_hash,
            "window_hash": self.window_hash,
            "runtime_hash": self.runtime_hash,
            "entry_hash": self.entry_hash,
            "status": self.status,
            "pipeline_status": (
                self.pipeline_status
            ),
        }

        for field_name, value in (
            required.items()
        ):
            if not str(value).strip():
                raise ValueError(
                    f"{field_name} must not "
                    "be empty"
                )

        if self.source_record_count < 0:
            raise ValueError(
                "source_record_count cannot "
                "be negative"
            )

        if self.in_window_record_count < 0:
            raise ValueError(
                "in_window_record_count cannot "
                "be negative"
            )

        if self.opportunity_count < 0:
            raise ValueError(
                "opportunity_count cannot "
                "be negative"
            )

        if self.read_only is not True:
            raise ValueError(
                "replay entry must be "
                "read-only"
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
            "sequence": self.sequence,
            "replay_id": self.replay_id,
            "observed_at": self.observed_at,
            "source_hash": self.source_hash,
            "window_hash": self.window_hash,
            "runtime_hash": self.runtime_hash,
            "previous_entry_hash": (
                self.previous_entry_hash
            ),
            "status": self.status,
            "accepted": self.accepted,
            "source_record_count": (
                self.source_record_count
            ),
            "in_window_record_count": (
                self.in_window_record_count
            ),
            "opportunity_count": (
                self.opportunity_count
            ),
            "pipeline_status": (
                self.pipeline_status
            ),
            "metadata": _metadata_dict(
                self.metadata
            ),
            "read_only": self.read_only,
        }

    def as_dict(self) -> Dict[str, Any]:
        payload = self.payload()
        payload["entry_hash"] = self.entry_hash
        return payload

    def verify_entry_hash(self) -> bool:
        return self.entry_hash == _stable_hash(
            self.payload()
        )


@dataclass(frozen=True)
class MarketRegimeReplayLedgerResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    observed_at: str
    entry_count: int
    entries: Tuple[
        MarketRegimeReplayEntry,
        ...,
    ]
    head_hash: str
    rejection_reasons: Tuple[str, ...]
    metadata: Tuple[
        Tuple[str, Any],
        ...,
    ] = field(
        default_factory=tuple
    )
    ledger_hash: str = ""
    read_only: bool = True

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                "invalid replay ledger "
                "schema_version"
            )

        if self.engine_id != ENGINE_ID:
            raise ValueError(
                "invalid replay ledger "
                "engine_id"
            )

        if self.status not in LEDGER_STATUSES:
            raise ValueError(
                "invalid replay ledger status"
            )

        if not str(self.observed_at).strip():
            raise ValueError(
                "observed_at must not be empty"
            )

        if self.entry_count < 0:
            raise ValueError(
                "entry_count cannot be negative"
            )

        if self.entry_count != len(
            self.entries
        ):
            raise ValueError(
                "entry_count does not match "
                "entries"
            )

        if self.read_only is not True:
            raise ValueError(
                "replay ledger must be "
                "read-only"
            )

        if self.accepted:
            if self.status not in {
                "recorded",
                "empty",
            }:
                raise ValueError(
                    "accepted ledger must have "
                    "recorded or empty status"
                )

            if self.rejection_reasons:
                raise ValueError(
                    "accepted ledger cannot "
                    "contain rejection reasons"
                )
        else:
            if self.status != "rejected":
                raise ValueError(
                    "rejected ledger must have "
                    "rejected status"
                )

            if not self.rejection_reasons:
                raise ValueError(
                    "rejected ledger must "
                    "contain rejection reasons"
                )

        if self.entries:
            if self.head_hash != (
                self.entries[-1].entry_hash
            ):
                raise ValueError(
                    "head_hash must match the "
                    "last entry hash"
                )
        else:
            if self.head_hash:
                raise ValueError(
                    "empty ledger cannot have "
                    "a head_hash"
                )

        sequences = [
            entry.sequence
            for entry in self.entries
        ]

        expected_sequences = list(
            range(
                1,
                len(self.entries) + 1,
            )
        )

        if sequences != expected_sequences:
            raise ValueError(
                "entry sequences must be "
                "contiguous"
            )

        replay_ids = [
            entry.replay_id
            for entry in self.entries
        ]

        if len(replay_ids) != len(
            set(replay_ids)
        ):
            raise ValueError(
                "replay identifiers must be "
                "unique"
            )

        if not str(self.ledger_hash).strip():
            raise ValueError(
                "ledger_hash must not be empty"
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
            "schema_version": (
                self.schema_version
            ),
            "engine_id": self.engine_id,
            "status": self.status,
            "accepted": self.accepted,
            "observed_at": self.observed_at,
            "entry_count": self.entry_count,
            "entries": tuple(
                entry.as_dict()
                for entry in self.entries
            ),
            "head_hash": self.head_hash,
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
        payload["ledger_hash"] = (
            self.ledger_hash
        )
        return payload

    def verify_ledger_hash(self) -> bool:
        return self.ledger_hash == _stable_hash(
            self.payload()
        )

    def verify_chain(self) -> bool:
        previous_hash = ""

        for entry in self.entries:
            if (
                entry.previous_entry_hash
                != previous_hash
            ):
                return False

            if not entry.verify_entry_hash():
                return False

            previous_hash = entry.entry_hash

        if self.entries:
            return self.head_hash == previous_hash

        return self.head_hash == ""


def build_market_regime_replay_entry(
    runtime_result: (
        MarketRegimeOOSRuntimeGateResult
    ),
    source_result: Any,
    window: MarketRegimeOOSWindow,
    sequence: int,
    previous_entry_hash: str = "",
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeReplayEntry:
    if not isinstance(
        runtime_result,
        MarketRegimeOOSRuntimeGateResult,
    ):
        raise TypeError(
            "runtime_result must be a "
            "MarketRegimeOOSRuntimeGateResult"
        )

    if not isinstance(
        window,
        MarketRegimeOOSWindow,
    ):
        raise TypeError(
            "window must be a "
            "MarketRegimeOOSWindow"
        )

    if sequence < 1:
        raise ValueError(
            "sequence must be at least 1"
        )

    source_hash = _stable_hash(
        _artifact_dict(source_result)
    )

    window_hash = _stable_hash(
        window.as_dict()
    )

    runtime_hash = (
        runtime_result.result_hash
    )

    replay_id = (
        "market-regime-replay-"
        + _stable_hash(
            {
                "source_hash": source_hash,
                "window_hash": window_hash,
                "runtime_hash": runtime_hash,
            }
        )[:24]
    )

    entry_metadata = {
        "runtime_schema_version": (
            runtime_result.schema_version
        ),
        "runtime_engine_id": (
            runtime_result.engine_id
        ),
        "runtime_read_only": (
            runtime_result.read_only
        ),
        "pipeline_hash": (
            runtime_result.pipeline_result
            .pipeline_hash
        ),
        "invalid_timestamp_record_count": (
            runtime_result
            .invalid_timestamp_record_count
        ),
        "deterministic": True,
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "read_only": True,
    }

    if metadata:
        for key, value in metadata.items():
            entry_metadata[str(key)] = (
                _stable_value(value)
            )

    normalized_metadata = _normalize_metadata(
        entry_metadata
    )

    payload = {
        "sequence": sequence,
        "replay_id": replay_id,
        "observed_at": (
            runtime_result.observed_at
        ),
        "source_hash": source_hash,
        "window_hash": window_hash,
        "runtime_hash": runtime_hash,
        "previous_entry_hash": (
            previous_entry_hash
        ),
        "status": runtime_result.status,
        "accepted": runtime_result.accepted,
        "source_record_count": (
            runtime_result.source_record_count
        ),
        "in_window_record_count": (
            runtime_result
            .in_window_record_count
        ),
        "opportunity_count": (
            runtime_result.pipeline_result
            .opportunity_count
        ),
        "pipeline_status": (
            runtime_result.pipeline_result
            .status
        ),
        "metadata": _metadata_dict(
            normalized_metadata
        ),
        "read_only": True,
    }

    entry = MarketRegimeReplayEntry(
        sequence=sequence,
        replay_id=replay_id,
        observed_at=(
            runtime_result.observed_at
        ),
        source_hash=source_hash,
        window_hash=window_hash,
        runtime_hash=runtime_hash,
        previous_entry_hash=(
            previous_entry_hash
        ),
        status=runtime_result.status,
        accepted=runtime_result.accepted,
        source_record_count=(
            runtime_result.source_record_count
        ),
        in_window_record_count=(
            runtime_result
            .in_window_record_count
        ),
        opportunity_count=(
            runtime_result.pipeline_result
            .opportunity_count
        ),
        pipeline_status=(
            runtime_result.pipeline_result
            .status
        ),
        entry_hash=_stable_hash(payload),
        metadata=normalized_metadata,
        read_only=True,
    )

    if not entry.verify_entry_hash():
        raise AssertionError(
            "replay entry produced an "
            "invalid deterministic hash"
        )

    return entry


def build_market_regime_replay_ledger(
    replay_runs: Iterable[
        Tuple[
            Any,
            MarketRegimeOOSWindow,
            Optional[str],
        ]
    ],
    metadata: Optional[
        Mapping[str, Any]
    ] = None,
) -> MarketRegimeReplayLedgerResult:
    runs = tuple(replay_runs or tuple())

    entries = []
    rejection_reasons = []
    previous_entry_hash = ""
    observed_at = (
        "1970-01-01T00:00:00+00:00"
    )

    for sequence, run in enumerate(
        runs,
        start=1,
    ):
        if (
            not isinstance(run, tuple)
            or len(run) != 3
        ):
            raise TypeError(
                "each replay run must be a "
                "(source_result, window, "
                "observed_at) tuple"
            )

        (
            source_result,
            window,
            run_observed_at,
        ) = run

        runtime_result = (
            evaluate_market_regime_oos_runtime(
                source_result=source_result,
                window=window,
                observed_at=run_observed_at,
                metadata={
                    "replay_sequence": (
                        sequence
                    ),
                },
            )
        )

        observed_at = (
            runtime_result.observed_at
        )

        runtime_validation = (
            validate_market_regime_oos_runtime_gate(
                runtime_result
            )
        )

        if (
            runtime_validation["accepted"]
            is not True
        ):
            rejection_reasons.append(
                "invalid_runtime_result"
            )

        if runtime_result.accepted is not True:
            rejection_reasons.append(
                "runtime_rejected"
            )

        entry = build_market_regime_replay_entry(
            runtime_result=runtime_result,
            source_result=source_result,
            window=window,
            sequence=sequence,
            previous_entry_hash=(
                previous_entry_hash
            ),
        )

        entries.append(entry)

        previous_entry_hash = (
            entry.entry_hash
        )

    normalized_rejections = tuple(
        sorted(
            set(rejection_reasons)
        )
    )

    accepted = not normalized_rejections

    if not accepted:
        status = "rejected"
    elif not entries:
        status = "empty"
    else:
        status = "recorded"

    ledger_metadata = {
        "ledger_mode": (
            "immutable_replay_projection"
        ),
        "chain_algorithm": "sha256",
        "entry_hash_chain": True,
        "external_state_mutated": False,
        "persistent_write_performed": False,
        "order_placement_performed": False,
        "transaction_signed": False,
        "deterministic": True,
        "immutable": True,
        "replayable": True,
        "explainable": True,
        "auditable": True,
        "read_only": True,
    }

    if metadata:
        for key, value in metadata.items():
            ledger_metadata[str(key)] = (
                _stable_value(value)
            )

    normalized_metadata = _normalize_metadata(
        ledger_metadata
    )

    normalized_entries = tuple(entries)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "accepted": accepted,
        "observed_at": observed_at,
        "entry_count": len(
            normalized_entries
        ),
        "entries": tuple(
            entry.as_dict()
            for entry in normalized_entries
        ),
        "head_hash": (
            normalized_entries[-1]
            .entry_hash
            if normalized_entries
            else ""
        ),
        "rejection_reasons": (
            normalized_rejections
        ),
        "metadata": _metadata_dict(
            normalized_metadata
        ),
        "read_only": True,
    }

    result = (
        MarketRegimeReplayLedgerResult(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            status=status,
            accepted=accepted,
            observed_at=observed_at,
            entry_count=len(
                normalized_entries
            ),
            entries=normalized_entries,
            head_hash=(
                normalized_entries[-1]
                .entry_hash
                if normalized_entries
                else ""
            ),
            rejection_reasons=(
                normalized_rejections
            ),
            metadata=normalized_metadata,
            ledger_hash=_stable_hash(
                payload
            ),
            read_only=True,
        )
    )

    if not result.verify_ledger_hash():
        raise AssertionError(
            "replay ledger produced an "
            "invalid deterministic hash"
        )

    if not result.verify_chain():
        raise AssertionError(
            "replay ledger produced an "
            "invalid hash chain"
        )

    return result


def replay_market_regime_entry(
    entry: MarketRegimeReplayEntry,
    source_result: Any,
    window: MarketRegimeOOSWindow,
) -> Dict[str, Any]:
    if not isinstance(
        entry,
        MarketRegimeReplayEntry,
    ):
        raise TypeError(
            "entry must be a "
            "MarketRegimeReplayEntry"
        )

    runtime_result = (
        evaluate_market_regime_oos_runtime(
            source_result=source_result,
            window=window,
            observed_at=entry.observed_at,
            metadata={
                "replay_sequence": (
                    entry.sequence
                ),
            },
        )
    )

    source_hash = _stable_hash(
        _artifact_dict(source_result)
    )

    window_hash = _stable_hash(
        window.as_dict()
    )

    checks = {
        "source_hash_match": (
            source_hash
            == entry.source_hash
        ),
        "window_hash_match": (
            window_hash
            == entry.window_hash
        ),
        "runtime_hash_match": (
            runtime_result.result_hash
            == entry.runtime_hash
        ),
        "status_match": (
            runtime_result.status
            == entry.status
        ),
        "accepted_match": (
            runtime_result.accepted
            == entry.accepted
        ),
        "pipeline_status_match": (
            runtime_result.pipeline_result
            .status
            == entry.pipeline_status
        ),
        "opportunity_count_match": (
            runtime_result.pipeline_result
            .opportunity_count
            == entry.opportunity_count
        ),
    }

    return {
        "accepted": all(
            checks.values()
        ),
        "checks": checks,
        "runtime_result": runtime_result,
    }


def validate_market_regime_replay_ledger(
    result: Any,
) -> Dict[str, Any]:
    checks = {
        "result_type": isinstance(
            result,
            MarketRegimeReplayLedgerResult,
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
            in LEDGER_STATUSES
        ),
        "read_only": (
            getattr(
                result,
                "read_only",
                None,
            )
            is True
        ),
        "ledger_hash_valid": (
            isinstance(
                result,
                MarketRegimeReplayLedgerResult,
            )
            and result.verify_ledger_hash()
        ),
        "chain_valid": (
            isinstance(
                result,
                MarketRegimeReplayLedgerResult,
            )
            and result.verify_chain()
        ),
        "entry_count_valid": (
            isinstance(
                result,
                MarketRegimeReplayLedgerResult,
            )
            and result.entry_count
            == len(result.entries)
        ),
    }

    return {
        "accepted": all(
            checks.values()
        ),
        "checks": checks,
    }


def assert_market_regime_replay_ledger_read_only(
    result: MarketRegimeReplayLedgerResult,
) -> bool:
    if not isinstance(
        result,
        MarketRegimeReplayLedgerResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimeReplayLedgerResult"
        )

    if READ_ONLY is not True:
        raise AssertionError(
            "market regime replay ledger "
            "must be read-only"
        )

    if result.read_only is not True:
        raise AssertionError(
            "replay ledger result must be "
            "read-only"
        )

    if not all(
        entry.read_only
        for entry in result.entries
    ):
        raise AssertionError(
            "all replay entries must be "
            "read-only"
        )

    metadata = dict(result.metadata)

    protected_flags = {
        "external_state_mutated": False,
        "persistent_write_performed": False,
        "order_placement_performed": False,
        "transaction_signed": False,
        "read_only": True,
    }

    for key, expected in (
        protected_flags.items()
    ):
        if metadata.get(key) is not expected:
            raise AssertionError(
                f"invalid read-only flag: {key}"
            )

    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "LEDGER_STATUSES",
    "MarketRegimeReplayEntry",
    "MarketRegimeReplayLedgerResult",
    "build_market_regime_replay_entry",
    "build_market_regime_replay_ledger",
    "replay_market_regime_entry",
    "validate_market_regime_replay_ledger",
    "assert_market_regime_replay_ledger_read_only",
]
