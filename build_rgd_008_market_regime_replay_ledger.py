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

MODULE = PACKAGE / "market_regime_replay_ledger.py"

TEST = ROOT / "test_rgd_008_market_regime_replay_ledger.py"

INIT = PACKAGE / "__init__.py"


MODULE.write_text(
r"""
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
""",
    encoding="utf-8",
)


TEST.write_text(
r"""
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_oos_runtime_gate import (
    MarketRegimeOOSWindow,
)

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_replay_ledger import (
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimeReplayEntry,
    MarketRegimeReplayLedgerResult,
    assert_market_regime_replay_ledger_read_only,
    build_market_regime_replay_entry,
    build_market_regime_replay_ledger,
    replay_market_regime_entry,
    validate_market_regime_replay_ledger,
)


TRAINING_END = "2026-07-01T23:59:59+00:00"
EVALUATION_START = "2026-07-02T00:00:00+00:00"
EVALUATION_END = "2026-07-10T23:59:59+00:00"
OBSERVED_AT = "2026-07-10T20:00:00+00:00"


def _window():
    return MarketRegimeOOSWindow(
        training_end=TRAINING_END,
        evaluation_start=EVALUATION_START,
        evaluation_end=EVALUATION_END,
    )


def _record(
    signal_id,
    signal_type,
    value,
    source_family,
    observed_at=OBSERVED_AT,
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
        "observed_at": observed_at,
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


def _second_source():
    source = _valid_source()

    source["records"] = tuple(
        {
            **record,
            "signal_id": (
                f"{record['signal_id']}-second"
            ),
            "source_hash": (
                f"{record['source_hash']}-second"
            ),
            "value": (
                float(record["value"]) * 0.95
            ),
        }
        for record in source["records"]
    )

    return source


def _rejected_source():
    source = _valid_source()

    source["records"] = (
        *source["records"],
        _record(
            signal_id="future-record",
            signal_type="volatility",
            value=0.50,
            source_family=(
                "volatility_discovery"
            ),
            observed_at=(
                "2026-07-11T12:00:00+00:00"
            ),
        ),
    )

    return source


def test_replay_ledger_constants():
    assert SCHEMA_VERSION == "RGD-008"

    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "replay_ledger"
    )

    assert READ_ONLY is True


def test_replay_ledger_records_single_run():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    assert isinstance(
        result,
        MarketRegimeReplayLedgerResult,
    )

    assert result.schema_version == "RGD-008"
    assert result.engine_id == ENGINE_ID
    assert result.status == "recorded"
    assert result.accepted is True
    assert result.entry_count == 1
    assert len(result.entries) == 1
    assert result.head_hash == (
        result.entries[0].entry_hash
    )
    assert result.rejection_reasons == tuple()
    assert result.verify_ledger_hash() is True
    assert result.verify_chain() is True
    assert result.read_only is True

    entry = result.entries[0]

    assert isinstance(
        entry,
        MarketRegimeReplayEntry,
    )

    assert entry.sequence == 1
    assert entry.previous_entry_hash == ""
    assert entry.status == "accepted"
    assert entry.accepted is True
    assert entry.source_record_count == 4
    assert entry.in_window_record_count == 4
    assert entry.opportunity_count == 1
    assert entry.pipeline_status == "completed"
    assert entry.verify_entry_hash() is True


def test_replay_ledger_records_chain():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
            (
                _second_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    assert result.status == "recorded"
    assert result.accepted is True
    assert result.entry_count == 2

    first = result.entries[0]
    second = result.entries[1]

    assert first.sequence == 1
    assert second.sequence == 2

    assert (
        second.previous_entry_hash
        == first.entry_hash
    )

    assert result.head_hash == (
        second.entry_hash
    )

    assert result.verify_chain() is True


def test_replay_ledger_empty():
    result = build_market_regime_replay_ledger(
        replay_runs=tuple(),
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.entry_count == 0
    assert result.entries == tuple()
    assert result.head_hash == ""
    assert result.rejection_reasons == tuple()
    assert result.verify_ledger_hash() is True
    assert result.verify_chain() is True


def test_replay_ledger_rejected_runtime():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _rejected_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.entry_count == 1

    assert (
        "runtime_rejected"
        in result.rejection_reasons
    )

    assert result.entries[0].accepted is False
    assert result.verify_chain() is True


def test_replay_entry_reproduces():
    ledger = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    replay = replay_market_regime_entry(
        entry=ledger.entries[0],
        source_result=_valid_source(),
        window=_window(),
    )

    assert replay["accepted"] is True

    assert all(
        replay["checks"].values()
    )

    assert (
        replay["runtime_result"].result_hash
        == ledger.entries[0].runtime_hash
    )


def test_replay_entry_detects_source_change():
    ledger = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    replay = replay_market_regime_entry(
        entry=ledger.entries[0],
        source_result=_second_source(),
        window=_window(),
    )

    assert replay["accepted"] is False

    assert (
        replay["checks"][
            "source_hash_match"
        ]
        is False
    )


def test_replay_ledger_deterministic():
    runs = (
        (
            _valid_source(),
            _window(),
            OBSERVED_AT,
        ),
        (
            _second_source(),
            _window(),
            OBSERVED_AT,
        ),
    )

    result_1 = (
        build_market_regime_replay_ledger(
            replay_runs=runs,
        )
    )

    result_2 = (
        build_market_regime_replay_ledger(
            replay_runs=runs,
        )
    )

    assert result_1 == result_2

    assert result_1.ledger_hash == (
        result_2.ledger_hash
    )

    assert result_1.head_hash == (
        result_2.head_hash
    )

    assert (
        result_1.entries[0].entry_hash
        == result_2.entries[0].entry_hash
    )


def test_replay_ledger_metadata():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
        metadata={
            "environment": "unit_test",
            "build": "RGD-008",
        },
    )

    metadata = dict(result.metadata)

    assert metadata["environment"] == (
        "unit_test"
    )

    assert metadata["build"] == "RGD-008"

    assert (
        metadata[
            "external_state_mutated"
        ]
        is False
    )

    assert (
        metadata[
            "persistent_write_performed"
        ]
        is False
    )

    assert metadata["read_only"] is True


def test_replay_ledger_validation():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    validation = (
        validate_market_regime_replay_ledger(
            result
        )
    )

    assert validation["accepted"] is True

    assert all(
        validation["checks"].values()
    )


def test_replay_ledger_read_only():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    assert (
        assert_market_regime_replay_ledger_read_only(
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
            "replay ledger must be immutable"
        )

    entry = result.entries[0]

    try:
        entry.status = "rejected"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "replay entry must be immutable"
        )


def test_replay_ledger_as_dict():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-008"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["status"] == "recorded"
    assert payload["accepted"] is True
    assert payload["entry_count"] == 1

    assert payload["ledger_hash"] == (
        result.ledger_hash
    )

    assert (
        payload["entries"][0]["entry_hash"]
        == result.entries[0].entry_hash
    )


def test_replay_ledger_requires_valid_run_tuple():
    try:
        build_market_regime_replay_ledger(
            replay_runs=(
                (_valid_source(),),
            ),
        )
    except TypeError as exc:
        assert str(exc) == (
            "each replay run must be a "
            "(source_result, window, "
            "observed_at) tuple"
        )
    else:
        raise AssertionError(
            "expected replay tuple validation"
        )


if __name__ == "__main__":
    test_replay_ledger_constants()
    test_replay_ledger_records_single_run()
    test_replay_ledger_records_chain()
    test_replay_ledger_empty()
    test_replay_ledger_rejected_runtime()
    test_replay_entry_reproduces()
    test_replay_entry_detects_source_change()
    test_replay_ledger_deterministic()
    test_replay_ledger_metadata()
    test_replay_ledger_validation()
    test_replay_ledger_read_only()
    test_replay_ledger_as_dict()
    test_replay_ledger_requires_valid_run_tuple()

    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
            (
                _second_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    print(
        "[PASS] RGD-008 "
        "Market Regime Replay Ledger"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "entries": result.entry_count,
            "chain_valid": (
                result.verify_chain()
            ),
            "head_hash": (
                result.head_hash[:16]
                if result.head_hash
                else ""
            ),
            "read_only": result.read_only,
        }
    )
""",
    encoding="utf-8",
)


existing_init = (
    INIT.read_text(
        encoding="utf-8"
    )
    if INIT.exists()
    else ""
)

replay_import = r"""
from .market_regime_replay_ledger import (
    ENGINE_ID as REPLAY_LEDGER_ENGINE_ID,
    LEDGER_STATUSES,
    READ_ONLY as REPLAY_LEDGER_READ_ONLY,
    SCHEMA_VERSION as REPLAY_LEDGER_SCHEMA_VERSION,
    MarketRegimeReplayEntry,
    MarketRegimeReplayLedgerResult,
    assert_market_regime_replay_ledger_read_only,
    build_market_regime_replay_entry,
    build_market_regime_replay_ledger,
    replay_market_regime_entry,
    validate_market_regime_replay_ledger,
)
"""

if (
    "from .market_regime_replay_ledger import"
    not in existing_init
):
    updated_init = (
        existing_init.rstrip()
        + "\n\n"
        + replay_import.strip()
        + "\n"
    )

    INIT.write_text(
        updated_init,
        encoding="utf-8",
    )


print("========================================")
print(" RGD-008 INSTALLER")
print(" Market Regime Replay Ledger")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] RGD-008 installed")
print()
print("Run:")
print(
    "py "
    "test_rgd_008_market_regime_"
    "replay_ledger.py"
)
