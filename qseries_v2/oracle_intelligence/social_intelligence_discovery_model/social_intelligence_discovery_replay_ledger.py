
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .social_intelligence_discovery_oos_runtime_gate import SocialIntelligenceDiscoveryOOSRuntimeGate

SCHEMA_VERSION = "SID-008"
LEDGER_ID = "oracle.discovery.ledger.social_intelligence_replay"
VOLATILE_KEYS = {"created_at", "checked_at", "started_at", "completed_at", "run_at", "timestamp"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_volatile(v: Any) -> Any:
    if isinstance(v, Mapping):
        return {str(k): _strip_volatile(x) for k, x in v.items() if str(k) not in VOLATILE_KEYS}
    if isinstance(v, list):
        return [_strip_volatile(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_strip_volatile(x) for x in v)
    return v


def _stable_text(v: Any) -> str:
    v = _strip_volatile(v)
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{str(k)}:{_stable_text(x)}" for k, x in sorted(v.items(), key=lambda i: str(i[0]))) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_stable_text(x) for x in v) + "]"
    return repr(v)


def _fingerprint(v: Any) -> str:
    return sha256(_stable_text(v).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SocialIntelligenceReplayLedgerEntry:
    schema_version: str
    ledger_id: str
    entry_id: str
    packet_id: str
    opportunity_id: str
    post_id: str
    topic: str
    platform: str
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
            "post_id": self.post_id,
            "topic": self.topic,
            "platform": self.platform,
            "registry_key": self.registry_key,
            "packet_fingerprint": self.packet_fingerprint,
            "payload_fingerprint": self.payload_fingerprint,
            "audit_fingerprint": self.audit_fingerprint,
            "replay_status": self.replay_status,
            "payload_summary": dict(self.payload_summary),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SocialIntelligenceReplayLedgerReport:
    schema_version: str
    ledger_id: str
    status: str
    entries: Tuple[SocialIntelligenceReplayLedgerEntry, ...]
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
class SocialIntelligenceReplayComparisonReport:
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


class SocialIntelligenceDiscoveryReplayLedger:
    schema_version = SCHEMA_VERSION
    ledger_id = LEDGER_ID
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "read_only": True,
            "accepts": "SID-007 OOS runtime packets",
            "emits": "immutable social intelligence replay ledger entries",
            "supports_replay_comparison": True,
            "deterministic": True,
            "canonicalizes_volatile_fields": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
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

    def record_packets(self, packets: Sequence[Any]) -> SocialIntelligenceReplayLedgerReport:
        started_at = _utc_now_iso()
        packet_tuple = tuple(packets or ())
        entries = tuple(sorted((self._entry_from_packet(p) for p in packet_tuple), key=lambda e: (e.registry_key, e.packet_id)))

        run_fingerprint = _fingerprint(tuple({
            "entry_id": e.entry_id,
            "packet_id": e.packet_id,
            "opportunity_id": e.opportunity_id,
            "post_id": e.post_id,
            "registry_key": e.registry_key,
            "packet_fingerprint": e.packet_fingerprint,
            "payload_fingerprint": e.payload_fingerprint,
            "audit_fingerprint": e.audit_fingerprint,
        } for e in entries))

        telemetry = MappingProxyType({
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
        })

        return SocialIntelligenceReplayLedgerReport(
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
        source_name: str = "social_intelligence_replay_ledger_source",
        min_social_score: float = 0.55,
    ) -> SocialIntelligenceReplayLedgerReport:
        gate = SocialIntelligenceDiscoveryOOSRuntimeGate(source_name=source_name, min_social_score=min_social_score)
        return self.record_packets(gate.run(raw_records).packets)

    def compare(self, baseline: SocialIntelligenceReplayLedgerReport, replay: SocialIntelligenceReplayLedgerReport) -> SocialIntelligenceReplayComparisonReport:
        started_at = _utc_now_iso()
        matching = baseline.run_fingerprint == replay.run_fingerprint and len(baseline.entries) == len(replay.entries)
        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "baseline_entries": len(baseline.entries),
            "replay_entries": len(replay.entries),
            "read_only": True,
        })
        return SocialIntelligenceReplayComparisonReport(
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

    def _entry_from_packet(self, packet: Any) -> SocialIntelligenceReplayLedgerEntry:
        payload = dict(getattr(packet, "payload", {}) or {})
        audit = dict(getattr(packet, "audit", {}) or {})
        canonical_payload = _strip_volatile(payload)
        canonical_audit = _strip_volatile(audit)

        packet_payload = {
            "packet_id": getattr(packet, "packet_id", None),
            "registry_key": getattr(packet, "registry_key", None),
            "opportunity_id": getattr(packet, "opportunity_id", None),
            "post_id": getattr(packet, "post_id", None),
            "topic": getattr(packet, "topic", None),
            "platform": getattr(packet, "platform", None),
            "pipeline_status": getattr(packet, "pipeline_status", None),
            "payload": canonical_payload,
            "audit": canonical_audit,
            "read_only": getattr(packet, "read_only", None),
        }

        payload_summary = MappingProxyType({
            "opportunity_type": canonical_payload.get("opportunity_type"),
            "source_engine_id": canonical_payload.get("source_engine_id"),
            "validation_required": canonical_payload.get("validation_required"),
            "ranking_required": canonical_payload.get("ranking_required"),
            "registry_required": canonical_payload.get("registry_required"),
            "execution_allowed": canonical_payload.get("execution_allowed"),
            "order_allowed": canonical_payload.get("order_allowed"),
            "position_sizing_allowed": canonical_payload.get("position_sizing_allowed"),
            "posting_allowed": canonical_payload.get("posting_allowed"),
            "dm_allowed": canonical_payload.get("dm_allowed"),
            "read_only": canonical_payload.get("read_only"),
        })

        packet_fingerprint = _fingerprint(packet_payload)

        return SocialIntelligenceReplayLedgerEntry(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            entry_id=f"replay.entry:{packet_fingerprint[:24]}",
            packet_id=str(packet_payload["packet_id"]),
            opportunity_id=str(packet_payload["opportunity_id"]),
            post_id=str(packet_payload["post_id"]),
            topic=str(packet_payload["topic"]),
            platform=str(packet_payload["platform"]),
            registry_key=str(packet_payload["registry_key"]),
            packet_fingerprint=packet_fingerprint,
            payload_fingerprint=_fingerprint(canonical_payload),
            audit_fingerprint=_fingerprint(canonical_audit),
            replay_status="recorded",
            payload_summary=payload_summary,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "LEDGER_ID",
    "SocialIntelligenceReplayLedgerEntry",
    "SocialIntelligenceReplayLedgerReport",
    "SocialIntelligenceReplayComparisonReport",
    "SocialIntelligenceDiscoveryReplayLedger",
]
