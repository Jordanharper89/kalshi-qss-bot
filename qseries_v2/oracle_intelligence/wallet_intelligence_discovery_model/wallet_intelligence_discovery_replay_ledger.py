"""
WDM-008 Wallet Intelligence Discovery Replay Ledger

Read-only replay ledger for wallet intelligence discovery runtime packets.

Canonical replay hashes exclude volatile timestamps so reversed input order
and fresh run timestamps still produce deterministic fingerprints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .wallet_intelligence_discovery_oos_runtime_gate import (
    WalletIntelligenceDiscoveryOOSRuntimeGate,
)


SCHEMA_VERSION = "WDM-008"
LEDGER_ID = "oracle.discovery.ledger.wallet_intelligence_replay"
LEDGER_NAME = "Wallet Intelligence Discovery Replay Ledger"

VOLATILE_KEYS = {
    "created_at",
    "checked_at",
    "started_at",
    "completed_at",
    "run_at",
    "timestamp",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_volatile(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(k): _strip_volatile(v)
            for k, v in value.items()
            if str(k) not in VOLATILE_KEYS
        }
    if isinstance(value, list):
        return [_strip_volatile(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_strip_volatile(v) for v in value)
    return value


def _stable_text(value: Any) -> str:
    value = _strip_volatile(value)
    if isinstance(value, Mapping):
        return "{" + ",".join(
            f"{str(k)}:{_stable_text(v)}"
            for k, v in sorted(value.items(), key=lambda x: str(x[0]))
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class WalletIntelligenceReplayLedgerEntry:
    schema_version: str
    ledger_id: str
    entry_id: str
    packet_id: str
    opportunity_id: str
    wallet: str
    chain: str
    symbol: str
    signal_type: str
    registry_key: str
    packet_fingerprint: str
    payload_fingerprint: str
    audit_fingerprint: str
    replay_status: str
    payload_summary: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "entry_id": self.entry_id,
            "packet_id": self.packet_id,
            "opportunity_id": self.opportunity_id,
            "wallet": self.wallet,
            "chain": self.chain,
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "registry_key": self.registry_key,
            "packet_fingerprint": self.packet_fingerprint,
            "payload_fingerprint": self.payload_fingerprint,
            "audit_fingerprint": self.audit_fingerprint,
            "replay_status": self.replay_status,
            "payload_summary": dict(self.payload_summary),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligenceReplayLedgerReport:
    schema_version: str
    ledger_id: str
    status: str
    entries: Tuple[WalletIntelligenceReplayLedgerEntry, ...]
    run_fingerprint: str
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "status": self.status,
            "entries": [e.to_dict() for e in self.entries],
            "run_fingerprint": self.run_fingerprint,
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligenceReplayComparisonReport:
    schema_version: str
    ledger_id: str
    status: str
    matching: bool
    baseline_fingerprint: str
    replay_fingerprint: str
    baseline_entries: int
    replay_entries: int
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "status": self.status,
            "matching": self.matching,
            "baseline_fingerprint": self.baseline_fingerprint,
            "replay_fingerprint": self.replay_fingerprint,
            "baseline_entries": self.baseline_entries,
            "replay_entries": self.replay_entries,
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class WalletIntelligenceDiscoveryReplayLedger:
    schema_version = SCHEMA_VERSION
    ledger_id = LEDGER_ID
    ledger_name = LEDGER_NAME
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "ledger_name": self.ledger_name,
            "read_only": True,
            "accepts": "WDM-007 OOS runtime packets",
            "emits": "immutable wallet intelligence replay ledger entries",
            "supports_replay_comparison": True,
            "deterministic": True,
            "canonicalizes_volatile_fields": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def record_packets(self, packets: Sequence[Any]) -> WalletIntelligenceReplayLedgerReport:
        started_at = _utc_now_iso()
        packet_tuple = tuple(packets or ())

        entries = tuple(
            sorted(
                (self._entry_from_packet(packet) for packet in packet_tuple),
                key=lambda e: (e.registry_key, e.packet_id, e.entry_id),
            )
        )

        run_fingerprint = _fingerprint(
            tuple(
                {
                    "entry_id": e.entry_id,
                    "packet_id": e.packet_id,
                    "opportunity_id": e.opportunity_id,
                    "wallet": e.wallet,
                    "chain": e.chain,
                    "symbol": e.symbol,
                    "signal_type": e.signal_type,
                    "registry_key": e.registry_key,
                    "packet_fingerprint": e.packet_fingerprint,
                    "payload_fingerprint": e.payload_fingerprint,
                    "audit_fingerprint": e.audit_fingerprint,
                }
                for e in entries
            )
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "ledger_id": self.ledger_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "packets_seen": len(packet_tuple),
                "entries_emitted": len(entries),
                "run_fingerprint": run_fingerprint,
                "read_only": True,
                "deterministic_sort": True,
                "volatile_fields_excluded": sorted(VOLATILE_KEYS),
            }
        )

        return WalletIntelligenceReplayLedgerReport(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            status="passed" if entries else "empty",
            entries=entries,
            run_fingerprint=run_fingerprint,
            telemetry=telemetry,
            read_only=True,
        )

    def run_discovery_and_record(
        self,
        raw_records: Sequence[Any] | None = None,
        source_name: str = "wallet_intelligence_replay_ledger_source",
        min_wallet_score: float = 0.70,
        min_usd_value: float = 1000.0,
        min_signal_score: float = 0.55,
    ) -> WalletIntelligenceReplayLedgerReport:
        gate = WalletIntelligenceDiscoveryOOSRuntimeGate(
            source_name=source_name,
            min_wallet_score=min_wallet_score,
            min_usd_value=min_usd_value,
            min_signal_score=min_signal_score,
        )
        runtime_report = gate.run(raw_records)
        return self.record_packets(runtime_report.packets)

    def compare(
        self,
        baseline: WalletIntelligenceReplayLedgerReport,
        replay: WalletIntelligenceReplayLedgerReport,
    ) -> WalletIntelligenceReplayComparisonReport:
        started_at = _utc_now_iso()
        matching = (
            baseline.run_fingerprint == replay.run_fingerprint
            and len(baseline.entries) == len(replay.entries)
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "ledger_id": self.ledger_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "baseline_entries": len(baseline.entries),
                "replay_entries": len(replay.entries),
                "read_only": True,
            }
        )

        return WalletIntelligenceReplayComparisonReport(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            status="matched" if matching else "mismatch",
            matching=matching,
            baseline_fingerprint=baseline.run_fingerprint,
            replay_fingerprint=replay.run_fingerprint,
            baseline_entries=len(baseline.entries),
            replay_entries=len(replay.entries),
            telemetry=telemetry,
            read_only=True,
        )

    def _entry_from_packet(self, packet: Any) -> WalletIntelligenceReplayLedgerEntry:
        payload = dict(getattr(packet, "payload", {}) or {})
        audit = dict(getattr(packet, "audit", {}) or {})

        canonical_payload = _strip_volatile(payload)
        canonical_audit = _strip_volatile(audit)

        packet_payload = {
            "packet_id": getattr(packet, "packet_id", None),
            "registry_key": getattr(packet, "registry_key", None),
            "opportunity_id": getattr(packet, "opportunity_id", None),
            "wallet": getattr(packet, "wallet", None),
            "chain": getattr(packet, "chain", None),
            "symbol": getattr(packet, "symbol", None),
            "signal_type": getattr(packet, "signal_type", None),
            "pipeline_status": getattr(packet, "pipeline_status", None),
            "payload": canonical_payload,
            "audit": canonical_audit,
            "read_only": getattr(packet, "read_only", None),
        }

        payload_summary = MappingProxyType(
            {
                "opportunity_type": canonical_payload.get("opportunity_type"),
                "source_engine_id": canonical_payload.get("source_engine_id"),
                "validation_required": canonical_payload.get("validation_required"),
                "ranking_required": canonical_payload.get("ranking_required"),
                "registry_required": canonical_payload.get("registry_required"),
                "execution_allowed": canonical_payload.get("execution_allowed"),
                "signing_allowed": canonical_payload.get("signing_allowed"),
                "fund_movement_allowed": canonical_payload.get("fund_movement_allowed"),
                "swap_allowed": canonical_payload.get("swap_allowed"),
                "read_only": canonical_payload.get("read_only"),
            }
        )

        packet_fingerprint = _fingerprint(packet_payload)
        payload_fingerprint = _fingerprint(canonical_payload)
        audit_fingerprint = _fingerprint(canonical_audit)
        entry_id = f"replay.entry:{packet_fingerprint[:24]}"

        return WalletIntelligenceReplayLedgerEntry(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            entry_id=entry_id,
            packet_id=str(packet_payload["packet_id"]),
            opportunity_id=str(packet_payload["opportunity_id"]),
            wallet=str(packet_payload["wallet"]),
            chain=str(packet_payload["chain"]),
            symbol=str(packet_payload["symbol"]),
            signal_type=str(packet_payload["signal_type"]),
            registry_key=str(packet_payload["registry_key"]),
            packet_fingerprint=packet_fingerprint,
            payload_fingerprint=payload_fingerprint,
            audit_fingerprint=audit_fingerprint,
            replay_status="recorded",
            payload_summary=payload_summary,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "LEDGER_ID",
    "LEDGER_NAME",
    "WalletIntelligenceReplayLedgerEntry",
    "WalletIntelligenceReplayLedgerReport",
    "WalletIntelligenceReplayComparisonReport",
    "WalletIntelligenceDiscoveryReplayLedger",
]
