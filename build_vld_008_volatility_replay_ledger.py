from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "volatility_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "volatility_replay_ledger.py"
TEST = ROOT / "test_vld_008_volatility_replay_ledger.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .volatility_oos_runtime_gate import (
    VolatilityOOSRuntimeGateResult,
    run_volatility_oos_runtime_gate,
)


READ_ONLY = True
SCHEMA_VERSION = "VLD-008"
ENGINE_ID = "oracle.discovery.volatility.replay_ledger"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_sort(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_deep_sort(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(v) for v in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return sha256(repr(_deep_sort(payload)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VolatilityReplayLedgerEntry:
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
class VolatilityReplayLedger:
    schema_version: str
    engine_id: str
    status: str
    entry_count: int
    accepted_count: int
    rejected_count: int
    entries: Tuple[VolatilityReplayLedgerEntry, ...]
    read_only: bool = True
    ledger_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["entries"] = [entry.canonical() for entry in self.entries]
        return _deep_sort(data)


class VolatilityReplayLedgerBuilder:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def entry_from_oos_result(
        self,
        result: VolatilityOOSRuntimeGateResult,
        sequence: int = 0,
        event_type: str = "volatility_oos_result",
    ) -> VolatilityReplayLedgerEntry:
        if not isinstance(result, VolatilityOOSRuntimeGateResult):
            raise TypeError("result must be a VolatilityOOSRuntimeGateResult")

        unsigned = VolatilityReplayLedgerEntry(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            sequence=int(sequence),
            event_type=str(event_type or "volatility_oos_result"),
            accepted=result.accepted,
            status=result.status,
            oos_hash=result.oos_hash,
            pipeline_hash=result.pipeline_hash,
            opportunity_count=result.opportunity_count,
            payload={
                "source_schema_version": result.schema_version,
                "source_engine_id": result.engine_id,
                "reason": result.reason,
                "checks": dict(result.checks),
                "runtime_context": dict(result.runtime_context),
            },
            read_only=True,
            entry_hash="",
        )

        return VolatilityReplayLedgerEntry(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            sequence=unsigned.sequence,
            event_type=unsigned.event_type,
            accepted=unsigned.accepted,
            status=unsigned.status,
            oos_hash=unsigned.oos_hash,
            pipeline_hash=unsigned.pipeline_hash,
            opportunity_count=unsigned.opportunity_count,
            payload=unsigned.payload,
            read_only=True,
            entry_hash=_stable_hash(unsigned.canonical()),
        )

    def build(self, results: Iterable[VolatilityOOSRuntimeGateResult]) -> VolatilityReplayLedger:
        entries = tuple(
            self.entry_from_oos_result(result, sequence=i)
            for i, result in enumerate(list(results or []))
        )
        return self.build_from_entries(entries)

    def build_from_entries(
        self,
        entries: Iterable[VolatilityReplayLedgerEntry],
    ) -> VolatilityReplayLedger:
        entry_tuple = tuple(sorted(entries or [], key=lambda e: e.sequence))
        accepted_count = sum(1 for entry in entry_tuple if entry.accepted)
        rejected_count = sum(1 for entry in entry_tuple if not entry.accepted)

        if rejected_count:
            status = "mixed" if accepted_count else "rejected"
        else:
            status = "accepted" if entry_tuple else "empty"

        unsigned = VolatilityReplayLedger(
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

        return VolatilityReplayLedger(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            entry_count=unsigned.entry_count,
            accepted_count=unsigned.accepted_count,
            rejected_count=unsigned.rejected_count,
            entries=unsigned.entries,
            read_only=True,
            ledger_hash=_stable_hash(unsigned.canonical()),
        )

    def replay(self, ledger: VolatilityReplayLedger) -> VolatilityReplayLedger:
        if not isinstance(ledger, VolatilityReplayLedger):
            raise TypeError("ledger must be a VolatilityReplayLedger")

        rebuilt_entries = []
        for entry in ledger.entries:
            unsigned = VolatilityReplayLedgerEntry(
                schema_version=entry.schema_version,
                engine_id=entry.engine_id,
                sequence=entry.sequence,
                event_type=entry.event_type,
                accepted=entry.accepted,
                status=entry.status,
                oos_hash=entry.oos_hash,
                pipeline_hash=entry.pipeline_hash,
                opportunity_count=entry.opportunity_count,
                payload=dict(entry.payload),
                read_only=True,
                entry_hash="",
            )
            rebuilt_entries.append(
                VolatilityReplayLedgerEntry(
                    schema_version=unsigned.schema_version,
                    engine_id=unsigned.engine_id,
                    sequence=unsigned.sequence,
                    event_type=unsigned.event_type,
                    accepted=unsigned.accepted,
                    status=unsigned.status,
                    oos_hash=unsigned.oos_hash,
                    pipeline_hash=unsigned.pipeline_hash,
                    opportunity_count=unsigned.opportunity_count,
                    payload=unsigned.payload,
                    read_only=True,
                    entry_hash=_stable_hash(unsigned.canonical()),
                )
            )

        return self.build_from_entries(tuple(rebuilt_entries))

    def validate(self, ledger: VolatilityReplayLedger) -> Dict[str, Any]:
        if not isinstance(ledger, VolatilityReplayLedger):
            raise TypeError("ledger must be a VolatilityReplayLedger")

        replayed = self.replay(ledger)
        checks = {
            "read_only": ledger.read_only is True,
            "schema_version": ledger.schema_version == self.schema_version,
            "engine_id": ledger.engine_id == self.engine_id,
            "entry_count_matches": ledger.entry_count == len(ledger.entries),
            "accepted_count_matches": ledger.accepted_count == sum(1 for e in ledger.entries if e.accepted),
            "rejected_count_matches": ledger.rejected_count == sum(1 for e in ledger.entries if not e.accepted),
            "entries_have_hashes": all(bool(e.entry_hash) for e in ledger.entries),
            "entries_read_only": all(e.read_only is True for e in ledger.entries),
            "replay_hash_matches": ledger.ledger_hash == replayed.ledger_hash,
        }

        return {
            "accepted": all(checks.values()),
            "checks": checks,
            "ledger_hash": ledger.ledger_hash,
            "replayed_hash": replayed.ledger_hash,
        }

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def build_volatility_replay_ledger(
    results: Iterable[VolatilityOOSRuntimeGateResult],
) -> VolatilityReplayLedger:
    return VolatilityReplayLedgerBuilder().build(results)


def run_volatility_replay_ledger(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "volatility.generic",
    observed_at: Optional[str] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> VolatilityReplayLedger:
    oos_result = run_volatility_oos_runtime_gate(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
        runtime_context=runtime_context,
    )
    return build_volatility_replay_ledger([oos_result])


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "VolatilityReplayLedgerEntry",
    "VolatilityReplayLedger",
    "VolatilityReplayLedgerBuilder",
    "build_volatility_replay_ledger",
    "run_volatility_replay_ledger",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_oos_runtime_gate import (
    run_volatility_oos_runtime_gate,
)
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_replay_ledger import (
    VolatilityReplayLedgerBuilder,
    build_volatility_replay_ledger,
    run_volatility_replay_ledger,
)


RAW = [
    {
        "market_id": "KXVOL-EXPAND",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.42,
        "implied_volatility": 0.20,
        "baseline_volatility": 0.20,
        "price_change": 0.08,
        "volume": 12000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    }
]


def test_volatility_replay_ledger_builds_valid_ledger():
    result = run_volatility_oos_runtime_gate(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "A"},
    )

    builder = VolatilityReplayLedgerBuilder()
    assert builder.assert_read_only() is True

    ledger = builder.build([result])

    assert ledger.schema_version == "VLD-008"
    assert ledger.engine_id == "oracle.discovery.volatility.replay_ledger"
    assert ledger.status == "accepted"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash
    assert ledger.entries[0].entry_hash
    assert ledger.entries[0].oos_hash == result.oos_hash
    assert ledger.entries[0].pipeline_hash == result.pipeline_hash


def test_volatility_replay_ledger_replays_exactly():
    result = run_volatility_oos_runtime_gate(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )

    builder = VolatilityReplayLedgerBuilder()
    ledger = builder.build([result])
    replayed = builder.replay(ledger)
    validation = builder.validate(ledger)

    assert replayed.ledger_hash == ledger.ledger_hash
    assert validation["accepted"] is True
    assert validation["checks"]["replay_hash_matches"] is True


def test_volatility_replay_ledger_handles_rejected_entry():
    rejected = run_volatility_oos_runtime_gate(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    ledger = build_volatility_replay_ledger([rejected])

    assert ledger.status == "rejected"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 1
    assert ledger.entries[0].accepted is False
    assert ledger.read_only is True


def test_volatility_replay_ledger_is_order_independent_for_pipeline_input():
    ledger1 = run_volatility_replay_ledger(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )
    ledger2 = run_volatility_replay_ledger(
        list(reversed(RAW)),
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    assert ledger1.ledger_hash == ledger2.ledger_hash


def test_volatility_replay_ledger_empty():
    ledger = build_volatility_replay_ledger([])

    assert ledger.status == "empty"
    assert ledger.entry_count == 0
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash


if __name__ == "__main__":
    test_volatility_replay_ledger_builds_valid_ledger()
    test_volatility_replay_ledger_replays_exactly()
    test_volatility_replay_ledger_handles_rejected_entry()
    test_volatility_replay_ledger_is_order_independent_for_pipeline_input()
    test_volatility_replay_ledger_empty()

    ledger = run_volatility_replay_ledger(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] VLD-008 Volatility Replay Ledger")
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

existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
exports = '''
from .volatility_replay_ledger import (
    VolatilityReplayLedger,
    VolatilityReplayLedgerBuilder,
    VolatilityReplayLedgerEntry,
    build_volatility_replay_ledger,
    run_volatility_replay_ledger,
)
'''
if "volatility_replay_ledger" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" VLD-008 INSTALLER")
print(" Volatility Replay Ledger")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] VLD-008 installed")
print()
print("Run:")
print("py test_vld_008_volatility_replay_ledger.py")