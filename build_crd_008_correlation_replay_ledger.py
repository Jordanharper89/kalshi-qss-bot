from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "correlation_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "correlation_replay_ledger.py"
TEST = ROOT / "test_crd_008_correlation_replay_ledger.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
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
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_oos_runtime_gate import (
    run_correlation_oos_runtime_gate,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_replay_ledger import (
    CorrelationReplayLedgerBuilder,
    build_correlation_replay_ledger,
    run_correlation_replay_ledger,
)


RAW = [
    {
        "primary_market_id": "KXTEST-A",
        "related_market_id": "KXTEST-B",
        "venue": "kalshi",
        "correlation": 0.82,
        "baseline_correlation": 0.80,
        "recent_correlation": 0.20,
        "lag": 0,
        "window": "30d",
        "sample_size": 120,
        "primary_return": 0.06,
        "related_return": -0.01,
        "observed_at": (
            "2026-07-09T00:00:00+00:00"
        ),
    },
    {
        "primary_market_id": "KXTEST-C",
        "related_market_id": "KXTEST-D",
        "venue": "kalshi",
        "correlation": -0.76,
        "baseline_correlation": -0.72,
        "recent_correlation": 0.31,
        "lag": 2,
        "window": "30d",
        "sample_size": 150,
        "primary_return": -0.03,
        "related_return": 0.04,
        "observed_at": (
            "2026-07-09T00:00:00+00:00"
        ),
    },
]


def _accepted_result():
    return run_correlation_oos_runtime_gate(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "oos",
            "fold": "A",
        },
    )


def _rejected_result():
    return run_correlation_oos_runtime_gate(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "oos",
            "execute": True,
        },
    )


def test_correlation_replay_ledger_builds_valid_ledger():
    result = _accepted_result()

    builder = CorrelationReplayLedgerBuilder()
    assert builder.assert_read_only() is True

    ledger = builder.build([result])

    assert ledger.schema_version == "CRD-008"
    assert (
        ledger.engine_id
        == (
            "oracle.discovery.correlation."
            "replay_ledger"
        )
    )
    assert ledger.status == "accepted"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash

    entry = ledger.entries[0]

    assert entry.sequence == 0
    assert entry.accepted is True
    assert entry.status == "accepted"
    assert entry.entry_hash
    assert entry.oos_hash == result.oos_hash
    assert (
        entry.pipeline_hash
        == result.pipeline_hash
    )
    assert (
        entry.opportunity_count
        == result.opportunity_count
    )
    assert entry.read_only is True


def test_correlation_replay_ledger_replays_exactly():
    result = _accepted_result()
    builder = CorrelationReplayLedgerBuilder()

    ledger = builder.build([result])
    replayed = builder.replay(ledger)
    validation = builder.validate(ledger)

    assert (
        replayed.ledger_hash
        == ledger.ledger_hash
    )
    assert (
        replayed.entries[0].entry_hash
        == ledger.entries[0].entry_hash
    )
    assert validation["accepted"] is True
    assert (
        validation["checks"][
            "replay_hash_matches"
        ]
        is True
    )


def test_correlation_replay_ledger_handles_rejected_entry():
    rejected = _rejected_result()

    ledger = build_correlation_replay_ledger(
        [rejected]
    )

    assert ledger.status == "rejected"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 1
    assert ledger.entries[0].accepted is False
    assert (
        ledger.entries[0].status
        == "rejected"
    )
    assert ledger.read_only is True
    assert ledger.ledger_hash


def test_correlation_replay_ledger_handles_mixed_entries():
    accepted = _accepted_result()
    rejected = _rejected_result()

    builder = CorrelationReplayLedgerBuilder()
    ledger = builder.build(
        [accepted, rejected]
    )

    assert ledger.status == "mixed"
    assert ledger.entry_count == 2
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 1
    assert [
        entry.sequence
        for entry in ledger.entries
    ] == [0, 1]

    validation = builder.validate(ledger)
    assert validation["accepted"] is True


def test_correlation_replay_ledger_is_order_independent_for_pipeline_input():
    ledger1 = run_correlation_replay_ledger(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "replay",
            "fold": "A",
        },
    )

    ledger2 = run_correlation_replay_ledger(
        list(reversed(RAW)),
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "fold": "A",
            "mode": "replay",
        },
    )

    assert (
        ledger1.ledger_hash
        == ledger2.ledger_hash
    )
    assert (
        ledger1.entries[0].entry_hash
        == ledger2.entries[0].entry_hash
    )


def test_correlation_replay_ledger_empty():
    ledger = build_correlation_replay_ledger([])

    assert ledger.status == "empty"
    assert ledger.entry_count == 0
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 0
    assert ledger.entries == tuple()
    assert ledger.read_only is True
    assert ledger.ledger_hash

    validation = (
        CorrelationReplayLedgerBuilder()
        .validate(ledger)
    )
    assert validation["accepted"] is True


def test_correlation_replay_ledger_rejects_invalid_inputs():
    builder = CorrelationReplayLedgerBuilder()

    try:
        builder.entry_from_oos_result(
            {"accepted": True}
        )
    except TypeError as exc:
        assert str(exc) == (
            "result must be a "
            "CorrelationOOSRuntimeGateResult"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid result"
        )

    try:
        builder.entry_from_oos_result(
            _accepted_result(),
            sequence=-1,
        )
    except ValueError as exc:
        assert str(exc) == (
            "sequence must be non-negative"
        )
    else:
        raise AssertionError(
            "expected ValueError for negative sequence"
        )

    try:
        builder.replay({"entries": []})
    except TypeError as exc:
        assert str(exc) == (
            "ledger must be a "
            "CorrelationReplayLedger"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid ledger"
        )


if __name__ == "__main__":
    test_correlation_replay_ledger_builds_valid_ledger()
    test_correlation_replay_ledger_replays_exactly()
    test_correlation_replay_ledger_handles_rejected_entry()
    test_correlation_replay_ledger_handles_mixed_entries()
    test_correlation_replay_ledger_is_order_independent_for_pipeline_input()
    test_correlation_replay_ledger_empty()
    test_correlation_replay_ledger_rejects_invalid_inputs()

    ledger = run_correlation_replay_ledger(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "oos",
        },
    )

    print(
        "[PASS] CRD-008 "
        "Correlation Replay Ledger"
    )
    print(
        {
            "schema_version": ledger.schema_version,
            "engine_id": ledger.engine_id,
            "status": ledger.status,
            "entries": ledger.entry_count,
            "accepted": ledger.accepted_count,
            "rejected": ledger.rejected_count,
            "read_only": ledger.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(
    encoding="utf-8"
) if INIT.exists() else ""

exports = '''
from .correlation_replay_ledger import (
    CorrelationReplayLedger,
    CorrelationReplayLedgerBuilder,
    CorrelationReplayLedgerEntry,
    build_correlation_replay_ledger,
    run_correlation_replay_ledger,
)
'''

if "correlation_replay_ledger" not in existing:
    INIT.write_text(
        existing.rstrip() + "\n" + exports.lstrip(),
        encoding="utf-8",
    )

print("========================================")
print(" CRD-008 INSTALLER")
print(" Correlation Replay Ledger")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] CRD-008 installed")
print()
print("Run:")
print("py test_crd_008_correlation_replay_ledger.py")