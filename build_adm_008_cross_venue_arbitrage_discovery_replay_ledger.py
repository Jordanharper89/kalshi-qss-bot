from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "arbitrage_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_FILE = MODULE_DIR / "cross_venue_arbitrage_discovery_replay_ledger.py"
TEST_FILE = ROOT / "test_adm_008_cross_venue_arbitrage_discovery_replay_ledger.py"
INIT_FILE = MODULE_DIR / "__init__.py"

LEDGER_CODE = r'''"""
ADM-008 Cross-Venue Arbitrage Discovery Replay Ledger

Read-only replay ledger for cross-venue arbitrage discovery runtime packets.

Canonical replay hashes exclude volatile timestamps so reversed input order
and fresh run timestamps still produce deterministic fingerprints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .cross_venue_arbitrage_discovery_oos_runtime_gate import (
    CrossVenueArbitrageDiscoveryOOSRuntimeGate,
)


SCHEMA_VERSION = "ADM-008"
LEDGER_ID = "oracle.discovery.ledger.cross_venue_arbitrage_replay"
LEDGER_NAME = "Cross-Venue Arbitrage Discovery Replay Ledger"

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
class CrossVenueArbitrageReplayLedgerEntry:
    schema_version: str
    ledger_id: str
    entry_id: str
    packet_id: str
    opportunity_id: str
    symbol: str
    buy_venue: str
    sell_venue: str
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
            "symbol": self.symbol,
            "buy_venue": self.buy_venue,
            "sell_venue": self.sell_venue,
            "registry_key": self.registry_key,
            "packet_fingerprint": self.packet_fingerprint,
            "payload_fingerprint": self.payload_fingerprint,
            "audit_fingerprint": self.audit_fingerprint,
            "replay_status": self.replay_status,
            "payload_summary": dict(self.payload_summary),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CrossVenueArbitrageReplayLedgerReport:
    schema_version: str
    ledger_id: str
    status: str
    entries: Tuple[CrossVenueArbitrageReplayLedgerEntry, ...]
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
class CrossVenueArbitrageReplayComparisonReport:
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


class CrossVenueArbitrageDiscoveryReplayLedger:
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
            "accepts": "ADM-007 OOS runtime packets",
            "emits": "immutable cross-venue arbitrage replay ledger entries",
            "supports_replay_comparison": True,
            "deterministic": True,
            "canonicalizes_volatile_fields": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "route_allowed": False,
            "leg_execution_allowed": False,
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

    def record_packets(self, packets: Sequence[Any]) -> CrossVenueArbitrageReplayLedgerReport:
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
                    "symbol": e.symbol,
                    "buy_venue": e.buy_venue,
                    "sell_venue": e.sell_venue,
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

        return CrossVenueArbitrageReplayLedgerReport(
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
        source_name: str = "cross_venue_arbitrage_replay_ledger_source",
        min_net_edge_percent: float = 0.001,
        min_liquidity: float = 1000.0,
    ) -> CrossVenueArbitrageReplayLedgerReport:
        gate = CrossVenueArbitrageDiscoveryOOSRuntimeGate(
            source_name=source_name,
            min_net_edge_percent=min_net_edge_percent,
            min_liquidity=min_liquidity,
        )
        runtime_report = gate.run(raw_records)
        return self.record_packets(runtime_report.packets)

    def compare(
        self,
        baseline: CrossVenueArbitrageReplayLedgerReport,
        replay: CrossVenueArbitrageReplayLedgerReport,
    ) -> CrossVenueArbitrageReplayComparisonReport:
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

        return CrossVenueArbitrageReplayComparisonReport(
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

    def _entry_from_packet(self, packet: Any) -> CrossVenueArbitrageReplayLedgerEntry:
        payload = dict(getattr(packet, "payload", {}) or {})
        audit = dict(getattr(packet, "audit", {}) or {})

        canonical_payload = _strip_volatile(payload)
        canonical_audit = _strip_volatile(audit)

        packet_payload = {
            "packet_id": getattr(packet, "packet_id", None),
            "registry_key": getattr(packet, "registry_key", None),
            "opportunity_id": getattr(packet, "opportunity_id", None),
            "symbol": getattr(packet, "symbol", None),
            "buy_venue": getattr(packet, "buy_venue", None),
            "sell_venue": getattr(packet, "sell_venue", None),
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
                "order_allowed": canonical_payload.get("order_allowed"),
                "route_allowed": canonical_payload.get("route_allowed"),
                "leg_execution_allowed": canonical_payload.get("leg_execution_allowed"),
                "read_only": canonical_payload.get("read_only"),
            }
        )

        packet_fingerprint = _fingerprint(packet_payload)
        payload_fingerprint = _fingerprint(canonical_payload)
        audit_fingerprint = _fingerprint(canonical_audit)
        entry_id = f"replay.entry:{packet_fingerprint[:24]}"

        return CrossVenueArbitrageReplayLedgerEntry(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            entry_id=entry_id,
            packet_id=str(packet_payload["packet_id"]),
            opportunity_id=str(packet_payload["opportunity_id"]),
            symbol=str(packet_payload["symbol"]),
            buy_venue=str(packet_payload["buy_venue"]),
            sell_venue=str(packet_payload["sell_venue"]),
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
    "CrossVenueArbitrageReplayLedgerEntry",
    "CrossVenueArbitrageReplayLedgerReport",
    "CrossVenueArbitrageReplayComparisonReport",
    "CrossVenueArbitrageDiscoveryReplayLedger",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_discovery_replay_ledger import (
    CrossVenueArbitrageDiscoveryReplayLedger,
)


def test_adm_008_cross_venue_arbitrage_discovery_replay_ledger():
    raw_records = [
        {
            "symbol": "BTC-USD",
            "venue": "coinbase",
            "bid": 65000,
            "ask": 65020,
            "last_price": 65010,
            "fee_bps": 8,
            "liquidity": 2500000,
            "volume_24h": 5000000,
            "latency_ms": 40,
            "status": "active",
        },
        {
            "symbol": "BTC/USD",
            "exchange": "kraken",
            "bid": 65300,
            "ask": 65320,
            "last": 65310,
            "taker_fee_bps": 10,
            "depth": 1500000,
            "volume": 4000000,
            "latency_ms": 80,
            "status": "active",
        },
        {
            "pair": "ETH/USD",
            "venue": "coinbase",
            "best_bid": 3500,
            "best_ask": 3502,
            "price": 3501,
            "fee_bps": 8,
            "liquidity": 800000,
            "volume_24h": 2000000,
            "status": "active",
        },
    ]

    ledger = CrossVenueArbitrageDiscoveryReplayLedger()
    caps = ledger.capabilities()
    health = ledger.health()

    baseline = ledger.run_discovery_and_record(
        raw_records,
        source_name="adm_008_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )
    replay = ledger.run_discovery_and_record(
        list(reversed(raw_records)),
        source_name="adm_008_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )
    comparison = ledger.compare(baseline, replay)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["route_allowed"] is False
    assert caps["leg_execution_allowed"] is False
    assert caps["deterministic"] is True
    assert caps["canonicalizes_volatile_fields"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert baseline.schema_version == "ADM-008"
    assert baseline.ledger_id == "oracle.discovery.ledger.cross_venue_arbitrage_replay"
    assert baseline.status == "passed"
    assert baseline.read_only is True
    assert len(baseline.entries) == 1

    assert baseline.run_fingerprint == replay.run_fingerprint
    assert comparison.matching is True
    assert comparison.status == "matched"
    assert comparison.read_only is True

    first = baseline.entries[0]
    assert first.read_only is True
    assert first.replay_status == "recorded"
    assert first.symbol == "BTC-USD"
    assert first.buy_venue == "coinbase"
    assert first.sell_venue == "kraken"
    assert first.packet_fingerprint
    assert first.payload_fingerprint
    assert first.audit_fingerprint
    assert first.payload_summary["validation_required"] is True
    assert first.payload_summary["ranking_required"] is True
    assert first.payload_summary["registry_required"] is True
    assert first.payload_summary["execution_allowed"] is False
    assert first.payload_summary["order_allowed"] is False
    assert first.payload_summary["route_allowed"] is False
    assert first.payload_summary["leg_execution_allowed"] is False
    assert first.payload_summary["read_only"] is True

    try:
        first.payload_summary["execution_allowed"] = True
        raise AssertionError("payload summary should be immutable")
    except TypeError:
        pass

    d = baseline.to_dict()
    c = comparison.to_dict()

    assert d["schema_version"] == "ADM-008"
    assert d["read_only"] is True
    assert d["telemetry"]["packets_seen"] == 1
    assert d["telemetry"]["entries_emitted"] == 1
    assert "created_at" in d["telemetry"]["volatile_fields_excluded"]
    assert c["matching"] is True
    assert c["baseline_entries"] == 1
    assert c["replay_entries"] == 1

    print("[PASS] ADM-008 Cross-Venue Arbitrage Discovery Replay Ledger")
    print(
        {
            "schema_version": d["schema_version"],
            "ledger_id": d["ledger_id"],
            "status": d["status"],
            "entries": len(d["entries"]),
            "replay_match": c["matching"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_adm_008_cross_venue_arbitrage_discovery_replay_ledger()
'''

INIT_EXPORT = '''
try:
    from .cross_venue_arbitrage_discovery_replay_ledger import (
        CrossVenueArbitrageDiscoveryReplayLedger,
        CrossVenueArbitrageReplayLedgerEntry,
        CrossVenueArbitrageReplayLedgerReport,
        CrossVenueArbitrageReplayComparisonReport,
    )
except Exception:
    pass
'''

LEDGER_FILE.write_text(LEDGER_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "CrossVenueArbitrageDiscoveryReplayLedger" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ADM-008 INSTALLER")
print(" Cross-Venue Arbitrage Discovery Replay Ledger")
print("========================================")
print(f"[OK] Wrote {LEDGER_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ADM-008 installed")
print()
print("Run:")
print("py test_adm_008_cross_venue_arbitrage_discovery_replay_ledger.py")