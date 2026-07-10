
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from .order_flow_oos_runtime_gate import (
    OrderFlowOOSRuntimeGateResult,
    run_order_flow_oos_runtime_gate,
)


READ_ONLY = True
SCHEMA_VERSION = "OFD-008"
ENGINE_ID = "oracle.discovery.order_flow.replay_ledger"


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
class OrderFlowReplayLedgerEntry:
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
class OrderFlowReplayLedger:
    schema_version: str
    engine_id: str
    status: str
    entry_count: int
    accepted_count: int
    rejected_count: int
    entries: Tuple[OrderFlowReplayLedgerEntry, ...]
    read_only: bool = True
    ledger_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["entries"] = [entry.canonical() for entry in self.entries]
        return _deep_sort(data)


class OrderFlowReplayLedgerBuilder:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def entry_from_oos_result(
        self,
        result: OrderFlowOOSRuntimeGateResult,
        sequence: int = 0,
        event_type: str = "order_flow_oos_result",
    ) -> OrderFlowReplayLedgerEntry:
        if not isinstance(result, OrderFlowOOSRuntimeGateResult):
            raise TypeError("result must be an OrderFlowOOSRuntimeGateResult")

        unsigned = OrderFlowReplayLedgerEntry(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            sequence=int(sequence),
            event_type=str(event_type or "order_flow_oos_result"),
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

        return OrderFlowReplayLedgerEntry(
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

    def build(self, results: Iterable[OrderFlowOOSRuntimeGateResult]) -> OrderFlowReplayLedger:
        result_list = list(results or [])
        entries = tuple(
            self.entry_from_oos_result(result, sequence=i)
            for i, result in enumerate(result_list)
        )

        accepted_count = sum(1 for entry in entries if entry.accepted)
        rejected_count = sum(1 for entry in entries if not entry.accepted)

        if rejected_count:
            status = "mixed" if accepted_count else "rejected"
        else:
            status = "accepted" if entries else "empty"

        unsigned = OrderFlowReplayLedger(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            entry_count=len(entries),
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            entries=entries,
            read_only=True,
            ledger_hash="",
        )

        return OrderFlowReplayLedger(
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

    def replay(self, ledger: OrderFlowReplayLedger) -> OrderFlowReplayLedger:
        if not isinstance(ledger, OrderFlowReplayLedger):
            raise TypeError("ledger must be an OrderFlowReplayLedger")

        rebuilt_entries = []
        for entry in ledger.entries:
            unsigned = OrderFlowReplayLedgerEntry(
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
                OrderFlowReplayLedgerEntry(
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

    def build_from_entries(
        self,
        entries: Iterable[OrderFlowReplayLedgerEntry],
    ) -> OrderFlowReplayLedger:
        entry_tuple = tuple(sorted(entries or [], key=lambda e: e.sequence))
        accepted_count = sum(1 for entry in entry_tuple if entry.accepted)
        rejected_count = sum(1 for entry in entry_tuple if not entry.accepted)

        if rejected_count:
            status = "mixed" if accepted_count else "rejected"
        else:
            status = "accepted" if entry_tuple else "empty"

        unsigned = OrderFlowReplayLedger(
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

        return OrderFlowReplayLedger(
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

    def validate(self, ledger: OrderFlowReplayLedger) -> Dict[str, Any]:
        if not isinstance(ledger, OrderFlowReplayLedger):
            raise TypeError("ledger must be an OrderFlowReplayLedger")

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


def build_order_flow_replay_ledger(
    results: Iterable[OrderFlowOOSRuntimeGateResult],
) -> OrderFlowReplayLedger:
    return OrderFlowReplayLedgerBuilder().build(results)


def run_order_flow_replay_ledger(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "order_flow.generic",
    observed_at: Optional[str] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> OrderFlowReplayLedger:
    oos_result = run_order_flow_oos_runtime_gate(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
        runtime_context=runtime_context,
    )
    return build_order_flow_replay_ledger([oos_result])


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OrderFlowReplayLedgerEntry",
    "OrderFlowReplayLedger",
    "OrderFlowReplayLedgerBuilder",
    "build_order_flow_replay_ledger",
    "run_order_flow_replay_ledger",
]
