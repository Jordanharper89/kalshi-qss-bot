
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .correlation_oos_runtime_gate import (
    CorrelationOOSRuntimeGateResult,
    run_correlation_oos_runtime_gate,
)


READ_ONLY = True
SCHEMA_VERSION = "CRD-008"
ENGINE_ID = "oracle.discovery.correlation.replay_ledger"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }
    if isinstance(value, list):
        return [_deep_sort(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(item) for item in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(_deep_sort(payload)).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CorrelationReplayLedgerEntry:
    schema_version: str
    engine_id: str
    sequence: int
    event_type: str
    accepted: bool
    status: str
    oos_hash: str
    pipeline_hash: str
    opportunity_count: int
    payload: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    entry_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


@dataclass(frozen=True)
class CorrelationReplayLedger:
    schema_version: str
    engine_id: str
    status: str
    entry_count: int
    accepted_count: int
    rejected_count: int
    entries: Tuple[CorrelationReplayLedgerEntry, ...]
    read_only: bool = True
    ledger_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["entries"] = [
            entry.canonical()
            for entry in self.entries
        ]
        return _deep_sort(data)


class CorrelationReplayLedgerBuilder:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def entry_from_oos_result(
        self,
        result: CorrelationOOSRuntimeGateResult,
        sequence: int = 0,
        event_type: str = "correlation_oos_result",
    ) -> CorrelationReplayLedgerEntry:
        if not isinstance(
            result,
            CorrelationOOSRuntimeGateResult,
        ):
            raise TypeError(
                "result must be a "
                "CorrelationOOSRuntimeGateResult"
            )

        if int(sequence) < 0:
            raise ValueError(
                "sequence must be non-negative"
            )

        unsigned = CorrelationReplayLedgerEntry(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            sequence=int(sequence),
            event_type=str(
                event_type or "correlation_oos_result"
            ),
            accepted=result.accepted,
            status=result.status,
            oos_hash=result.oos_hash,
            pipeline_hash=result.pipeline_hash,
            opportunity_count=result.opportunity_count,
            payload={
                "source_schema_version": (
                    result.schema_version
                ),
                "source_engine_id": result.engine_id,
                "reason": result.reason,
                "checks": dict(result.checks),
                "runtime_context": dict(
                    result.runtime_context
                ),
            },
            read_only=True,
            entry_hash="",
        )

        return CorrelationReplayLedgerEntry(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            sequence=unsigned.sequence,
            event_type=unsigned.event_type,
            accepted=unsigned.accepted,
            status=unsigned.status,
            oos_hash=unsigned.oos_hash,
            pipeline_hash=unsigned.pipeline_hash,
            opportunity_count=(
                unsigned.opportunity_count
            ),
            payload=unsigned.payload,
            read_only=True,
            entry_hash=_stable_hash(
                unsigned.canonical()
            ),
        )

    def build(
        self,
        results: Iterable[
            CorrelationOOSRuntimeGateResult
        ],
    ) -> CorrelationReplayLedger:
        result_list = list(results or [])

        entries = tuple(
            self.entry_from_oos_result(
                result=result,
                sequence=index,
            )
            for index, result in enumerate(result_list)
        )

        return self.build_from_entries(entries)

    def build_from_entries(
        self,
        entries: Iterable[
            CorrelationReplayLedgerEntry
        ],
    ) -> CorrelationReplayLedger:
        entry_list = list(entries or [])

        for entry in entry_list:
            if not isinstance(
                entry,
                CorrelationReplayLedgerEntry,
            ):
                raise TypeError(
                    "all entries must be "
                    "CorrelationReplayLedgerEntry instances"
                )

        entry_tuple = tuple(
            sorted(
                entry_list,
                key=lambda entry: entry.sequence,
            )
        )

        sequences = [
            entry.sequence
            for entry in entry_tuple
        ]

        if len(sequences) != len(set(sequences)):
            raise ValueError(
                "ledger entry sequences must be unique"
            )

        accepted_count = sum(
            1
            for entry in entry_tuple
            if entry.accepted
        )

        rejected_count = sum(
            1
            for entry in entry_tuple
            if not entry.accepted
        )

        if rejected_count:
            status = (
                "mixed"
                if accepted_count
                else "rejected"
            )
        else:
            status = (
                "accepted"
                if entry_tuple
                else "empty"
            )

        unsigned = CorrelationReplayLedger(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            entry_count=len(entry_tuple),
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            entries=entry_tuple,
            read_only=True,
            ledger_hash="",
        )

        return CorrelationReplayLedger(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            entry_count=unsigned.entry_count,
            accepted_count=unsigned.accepted_count,
            rejected_count=unsigned.rejected_count,
            entries=unsigned.entries,
            read_only=True,
            ledger_hash=_stable_hash(
                unsigned.canonical()
            ),
        )

    def replay(
        self,
        ledger: CorrelationReplayLedger,
    ) -> CorrelationReplayLedger:
        if not isinstance(
            ledger,
            CorrelationReplayLedger,
        ):
            raise TypeError(
                "ledger must be a "
                "CorrelationReplayLedger"
            )

        rebuilt_entries = []

        for entry in ledger.entries:
            unsigned = CorrelationReplayLedgerEntry(
                schema_version=entry.schema_version,
                engine_id=entry.engine_id,
                sequence=entry.sequence,
                event_type=entry.event_type,
                accepted=entry.accepted,
                status=entry.status,
                oos_hash=entry.oos_hash,
                pipeline_hash=entry.pipeline_hash,
                opportunity_count=(
                    entry.opportunity_count
                ),
                payload=dict(entry.payload),
                read_only=True,
                entry_hash="",
            )

            rebuilt_entries.append(
                CorrelationReplayLedgerEntry(
                    schema_version=unsigned.schema_version,
                    engine_id=unsigned.engine_id,
                    sequence=unsigned.sequence,
                    event_type=unsigned.event_type,
                    accepted=unsigned.accepted,
                    status=unsigned.status,
                    oos_hash=unsigned.oos_hash,
                    pipeline_hash=unsigned.pipeline_hash,
                    opportunity_count=(
                        unsigned.opportunity_count
                    ),
                    payload=unsigned.payload,
                    read_only=True,
                    entry_hash=_stable_hash(
                        unsigned.canonical()
                    ),
                )
            )

        return self.build_from_entries(
            tuple(rebuilt_entries)
        )

    def validate(
        self,
        ledger: CorrelationReplayLedger,
    ) -> Dict[str, Any]:
        if not isinstance(
            ledger,
            CorrelationReplayLedger,
        ):
            raise TypeError(
                "ledger must be a "
                "CorrelationReplayLedger"
            )

        replayed = self.replay(ledger)

        sequences = [
            entry.sequence
            for entry in ledger.entries
        ]

        checks = {
            "read_only": ledger.read_only is True,
            "schema_version": (
                ledger.schema_version
                == self.schema_version
            ),
            "engine_id": (
                ledger.engine_id
                == self.engine_id
            ),
            "valid_status": (
                ledger.status
                in {
                    "empty",
                    "accepted",
                    "rejected",
                    "mixed",
                }
            ),
            "entry_count_matches": (
                ledger.entry_count
                == len(ledger.entries)
            ),
            "accepted_count_matches": (
                ledger.accepted_count
                == sum(
                    1
                    for entry in ledger.entries
                    if entry.accepted
                )
            ),
            "rejected_count_matches": (
                ledger.rejected_count
                == sum(
                    1
                    for entry in ledger.entries
                    if not entry.accepted
                )
            ),
            "entries_have_hashes": all(
                bool(entry.entry_hash)
                for entry in ledger.entries
            ),
            "entries_have_oos_hashes": all(
                bool(entry.oos_hash)
                for entry in ledger.entries
            ),
            "entries_have_pipeline_hashes": all(
                bool(entry.pipeline_hash)
                for entry in ledger.entries
            ),
            "entries_read_only": all(
                entry.read_only is True
                for entry in ledger.entries
            ),
            "entry_schemas_match": all(
                entry.schema_version
                == self.schema_version
                for entry in ledger.entries
            ),
            "entry_engines_match": all(
                entry.engine_id
                == self.engine_id
                for entry in ledger.entries
            ),
            "sequences_unique": (
                len(sequences)
                == len(set(sequences))
            ),
            "sequences_sorted": (
                sequences == sorted(sequences)
            ),
            "ledger_hash_present": bool(
                ledger.ledger_hash
            ),
            "replay_hash_matches": (
                ledger.ledger_hash
                == replayed.ledger_hash
            ),
        }

        return {
            "accepted": all(checks.values()),
            "checks": checks,
            "ledger_hash": ledger.ledger_hash,
            "replayed_hash": (
                replayed.ledger_hash
            ),
            "entry_count": ledger.entry_count,
        }

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "oos_result_ledger_entries",
                "accepted_result_recording",
                "rejected_result_recording",
                "mixed_result_ledgers",
                "deterministic_entry_hashing",
                "deterministic_ledger_hashing",
                "exact_replay_validation",
                "immutable_audit_payloads",
            ],
        }

    def assert_read_only(self) -> bool:
        forbidden = [
            "buy",
            "sell",
            "trade",
            "execute",
            "order",
            "sign",
            "submit",
            "broadcast",
        ]

        offenders = sorted(
            word
            for word in forbidden
            if word in set(dir(self))
        )

        if offenders:
            raise AssertionError(
                f"mutation-like methods are forbidden: "
                f"{offenders}"
            )

        return True


def build_correlation_replay_ledger(
    results: Iterable[
        CorrelationOOSRuntimeGateResult
    ],
) -> CorrelationReplayLedger:
    return CorrelationReplayLedgerBuilder().build(
        results
    )


def run_correlation_replay_ledger(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "correlation.generic",
    observed_at: Optional[str] = None,
    runtime_context: Optional[
        Mapping[str, Any]
    ] = None,
    strong_correlation_threshold: float = 0.70,
    correlation_break_threshold: float = 0.30,
    return_divergence_threshold: float = 0.04,
    min_sample_size: int = 20,
    max_opportunities: int = 10000,
) -> CorrelationReplayLedger:
    oos_result = run_correlation_oos_runtime_gate(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
        runtime_context=runtime_context,
        strong_correlation_threshold=(
            strong_correlation_threshold
        ),
        correlation_break_threshold=(
            correlation_break_threshold
        ),
        return_divergence_threshold=(
            return_divergence_threshold
        ),
        min_sample_size=min_sample_size,
        max_opportunities=max_opportunities,
    )

    return build_correlation_replay_ledger(
        [oos_result]
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationReplayLedgerEntry",
    "CorrelationReplayLedger",
    "CorrelationReplayLedgerBuilder",
    "build_correlation_replay_ledger",
    "run_correlation_replay_ledger",
]
