from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "liquidity_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "liquidity_replay_ledger.py"
TEST = ROOT / "test_lqd_008_liquidity_replay_ledger.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .liquidity_oos_runtime_gate import (
    LiquidityOOSRuntimeGateResult,
    run_liquidity_oos_runtime_gate,
)


READ_ONLY = True
SCHEMA_VERSION = "LQD-008"
ENGINE_ID = "oracle.discovery.liquidity.replay_ledger"


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
class LiquidityReplayLedgerEntry:
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
class LiquidityReplayLedger:
    schema_version: str
    engine_id: str
    status: str
    entry_count: int
    accepted_count: int
    rejected_count: int
    entries: Tuple[LiquidityReplayLedgerEntry, ...]
    read_only: bool = True
    ledger_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["entries"] = [entry.canonical() for entry in self.entries]
        return _deep_sort(data)


class LiquidityReplayLedgerBuilder:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def entry_from_oos_result(
        self,
        result: LiquidityOOSRuntimeGateResult,
        sequence: int = 0,
        event_type: str = "liquidity_oos_result",
    ) -> LiquidityReplayLedgerEntry:
        if not isinstance(result, LiquidityOOSRuntimeGateResult):
            raise TypeError("result must be a LiquidityOOSRuntimeGateResult")

        unsigned = LiquidityReplayLedgerEntry(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            sequence=int(sequence),
            event_type=str(event_type or "liquidity_oos_result"),
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

        return LiquidityReplayLedgerEntry(
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

    def build(self, results: Iterable[LiquidityOOSRuntimeGateResult]) -> LiquidityReplayLedger:
        entries = tuple(self.entry_from_oos_result(result, sequence=i) for i, result in enumerate(list(results or [])))
        return self.build_from_entries(entries)

    def build_from_entries(self, entries: Iterable[LiquidityReplayLedgerEntry]) -> LiquidityReplayLedger:
        entry_tuple = tuple(sorted(entries or [], key=lambda e: e.sequence))
        accepted_count = sum(1 for entry in entry_tuple if entry.accepted)
        rejected_count = sum(1 for entry in entry_tuple if not entry.accepted)

        if rejected_count:
            status = "mixed" if accepted_count else "rejected"
        else:
            status = "accepted" if entry_tuple else "empty"

        unsigned = LiquidityReplayLedger(
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

        return LiquidityReplayLedger(
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

    def replay(self, ledger: LiquidityReplayLedger) -> LiquidityReplayLedger:
        if not isinstance(ledger, LiquidityReplayLedger):
            raise TypeError("ledger must be a LiquidityReplayLedger")

        rebuilt_entries = []
        for entry in ledger.entries:
            unsigned = LiquidityReplayLedgerEntry(
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
                LiquidityReplayLedgerEntry(
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

    def validate(self, ledger: LiquidityReplayLedger) -> Dict[str, Any]:
        if not isinstance(ledger, LiquidityReplayLedger):
            raise TypeError("ledger must be a LiquidityReplayLedger")

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


def build_liquidity_replay_ledger(
    results: Iterable[LiquidityOOSRuntimeGateResult],
) -> LiquidityReplayLedger:
    return LiquidityReplayLedgerBuilder().build(results)


def run_liquidity_replay_ledger(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "liquidity.generic",
    observed_at: Optional[str] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> LiquidityReplayLedger:
    oos_result = run_liquidity_oos_runtime_gate(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
        runtime_context=runtime_context,
    )
    return build_liquidity_replay_ledger([oos_result])


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "LiquidityReplayLedgerEntry",
    "LiquidityReplayLedger",
    "LiquidityReplayLedgerBuilder",
    "build_liquidity_replay_ledger",
    "run_liquidity_replay_ledger",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_oos_runtime_gate import (
    run_liquidity_oos_runtime_gate,
)
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_replay_ledger import (
    LiquidityReplayLedgerBuilder,
    build_liquidity_replay_ledger,
    run_liquidity_replay_ledger,
)


RAW = [
    {
        "market_id": "KXTHIN",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.40,
        "ask_price": 0.48,
        "bid_depth": 100,
        "ask_depth": 50,
        "volume_24h": 12000,
        "open_interest": 50000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    }
]


def test_liquidity_replay_ledger_builds_valid_ledger():
    result = run_liquidity_oos_runtime_gate(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "A"},
    )

    builder = LiquidityReplayLedgerBuilder()
    assert builder.assert_read_only() is True

    ledger = builder.build([result])

    assert ledger.schema_version == "LQD-008"
    assert ledger.engine_id == "oracle.discovery.liquidity.replay_ledger"
    assert ledger.status == "accepted"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash
    assert ledger.entries[0].entry_hash
    assert ledger.entries[0].oos_hash == result.oos_hash
    assert ledger.entries[0].pipeline_hash == result.pipeline_hash


def test_liquidity_replay_ledger_replays_exactly():
    result = run_liquidity_oos_runtime_gate(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )

    builder = LiquidityReplayLedgerBuilder()
    ledger = builder.build([result])
    replayed = builder.replay(ledger)
    validation = builder.validate(ledger)

    assert replayed.ledger_hash == ledger.ledger_hash
    assert validation["accepted"] is True
    assert validation["checks"]["replay_hash_matches"] is True


def test_liquidity_replay_ledger_handles_rejected_entry():
    rejected = run_liquidity_oos_runtime_gate(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    ledger = build_liquidity_replay_ledger([rejected])

    assert ledger.status == "rejected"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 1
    assert ledger.entries[0].accepted is False
    assert ledger.read_only is True


def test_liquidity_replay_ledger_is_order_independent_for_pipeline_input():
    ledger1 = run_liquidity_replay_ledger(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )
    ledger2 = run_liquidity_replay_ledger(
        list(reversed(RAW)),
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    assert ledger1.ledger_hash == ledger2.ledger_hash


def test_liquidity_replay_ledger_empty():
    ledger = build_liquidity_replay_ledger([])

    assert ledger.status == "empty"
    assert ledger.entry_count == 0
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash


if __name__ == "__main__":
    test_liquidity_replay_ledger_builds_valid_ledger()
    test_liquidity_replay_ledger_replays_exactly()
    test_liquidity_replay_ledger_handles_rejected_entry()
    test_liquidity_replay_ledger_is_order_independent_for_pipeline_input()
    test_liquidity_replay_ledger_empty()

    ledger = run_liquidity_replay_ledger(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] LQD-008 Liquidity Replay Ledger")
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
from .liquidity_replay_ledger import (
    LiquidityReplayLedger,
    LiquidityReplayLedgerBuilder,
    LiquidityReplayLedgerEntry,
    build_liquidity_replay_ledger,
    run_liquidity_replay_ledger,
)
'''
if "liquidity_replay_ledger" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" LQD-008 INSTALLER")
print(" Liquidity Replay Ledger")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] LQD-008 installed")
print()
print("Run:")
print("py test_lqd_008_liquidity_replay_ledger.py")