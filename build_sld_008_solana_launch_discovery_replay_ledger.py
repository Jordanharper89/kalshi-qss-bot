from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "solana_launch_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_FILE = MODULE_DIR / "solana_launch_discovery_replay_ledger.py"
TEST_FILE = ROOT / "test_sld_008_solana_launch_discovery_replay_ledger.py"
INIT_FILE = MODULE_DIR / "__init__.py"

LEDGER_CODE = r'''"""
SLD-008 Solana Launch Discovery Replay Ledger

Read-only replay ledger for Solana launch discovery runtime packets.

Canonical replay hashes exclude volatile timestamps so reversed input order
and fresh run timestamps still produce deterministic fingerprints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .solana_launch_discovery_oos_runtime_gate import SolanaLaunchDiscoveryOOSRuntimeGate


SCHEMA_VERSION = "SLD-008"
LEDGER_ID = "oracle.discovery.ledger.solana_launch_replay"
LEDGER_NAME = "Solana Launch Discovery Replay Ledger"

VOLATILE_KEYS = {
    "created_at",
    "checked_at",
    "started_at",
    "completed_at",
    "run_at",
    "timestamp",
    "detected_at",
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
class SolanaLaunchReplayLedgerEntry:
    schema_version: str
    ledger_id: str
    entry_id: str
    packet_id: str
    opportunity_id: str
    mint: str
    symbol: str
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
            "mint": self.mint,
            "symbol": self.symbol,
            "registry_key": self.registry_key,
            "packet_fingerprint": self.packet_fingerprint,
            "payload_fingerprint": self.payload_fingerprint,
            "audit_fingerprint": self.audit_fingerprint,
            "replay_status": self.replay_status,
            "payload_summary": dict(self.payload_summary),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SolanaLaunchReplayLedgerReport:
    schema_version: str
    ledger_id: str
    status: str
    entries: Tuple[SolanaLaunchReplayLedgerEntry, ...]
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
class SolanaLaunchReplayComparisonReport:
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


class SolanaLaunchDiscoveryReplayLedger:
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
            "accepts": "SLD-007 OOS runtime packets",
            "emits": "immutable Solana launch replay ledger entries",
            "supports_replay_comparison": True,
            "deterministic": True,
            "canonicalizes_volatile_fields": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
            "snipe_allowed": False,
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

    def record_packets(self, packets: Sequence[Any]) -> SolanaLaunchReplayLedgerReport:
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
                    "mint": e.mint,
                    "symbol": e.symbol,
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

        return SolanaLaunchReplayLedgerReport(
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
        source_name: str = "solana_launch_replay_ledger_source",
        min_liquidity_usd: float = 1000.0,
        max_age_seconds: float = 600.0,
        min_launch_score: float = 0.55,
    ) -> SolanaLaunchReplayLedgerReport:
        gate = SolanaLaunchDiscoveryOOSRuntimeGate(
            source_name=source_name,
            min_liquidity_usd=min_liquidity_usd,
            max_age_seconds=max_age_seconds,
            min_launch_score=min_launch_score,
        )
        runtime_report = gate.run(raw_records)
        return self.record_packets(runtime_report.packets)

    def compare(
        self,
        baseline: SolanaLaunchReplayLedgerReport,
        replay: SolanaLaunchReplayLedgerReport,
    ) -> SolanaLaunchReplayComparisonReport:
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

        return SolanaLaunchReplayComparisonReport(
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

    def _entry_from_packet(self, packet: Any) -> SolanaLaunchReplayLedgerEntry:
        payload = dict(getattr(packet, "payload", {}) or {})
        audit = dict(getattr(packet, "audit", {}) or {})

        canonical_payload = _strip_volatile(payload)
        canonical_audit = _strip_volatile(audit)

        packet_payload = {
            "packet_id": getattr(packet, "packet_id", None),
            "registry_key": getattr(packet, "registry_key", None),
            "opportunity_id": getattr(packet, "opportunity_id", None),
            "mint": getattr(packet, "mint", None),
            "symbol": getattr(packet, "symbol", None),
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
                "snipe_allowed": canonical_payload.get("snipe_allowed"),
                "read_only": canonical_payload.get("read_only"),
            }
        )

        packet_fingerprint = _fingerprint(packet_payload)
        payload_fingerprint = _fingerprint(canonical_payload)
        audit_fingerprint = _fingerprint(canonical_audit)
        entry_id = f"replay.entry:{packet_fingerprint[:24]}"

        return SolanaLaunchReplayLedgerEntry(
            schema_version=self.schema_version,
            ledger_id=self.ledger_id,
            entry_id=entry_id,
            packet_id=str(packet_payload["packet_id"]),
            opportunity_id=str(packet_payload["opportunity_id"]),
            mint=str(packet_payload["mint"]),
            symbol=str(packet_payload["symbol"]),
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
    "SolanaLaunchReplayLedgerEntry",
    "SolanaLaunchReplayLedgerReport",
    "SolanaLaunchReplayComparisonReport",
    "SolanaLaunchDiscoveryReplayLedger",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_replay_ledger import (
    SolanaLaunchDiscoveryReplayLedger,
)


def test_sld_008_solana_launch_discovery_replay_ledger():
    raw_records = [
        {
            "token_mint": "mint_a",
            "ticker": "ALPHA",
            "name": "Alpha Token",
            "pool_address": "pool_a",
            "dex": "raydium",
            "quote_asset": "SOL",
            "liquidity_usd": 50000,
            "market_cap_usd": 200000,
            "volume_5m_usd": 15000,
            "holder_count": 250,
            "age_seconds": 30,
            "mint_authority_disabled": True,
            "freeze_authority_disabled": True,
            "lp_burned": True,
            "pool_status": "active",
            "deployer_wallet": "wallet_a",
            "tx_signature": "tx_a",
            "detected_at": "2026-01-01T00:01:00Z",
        },
        {
            "mint": "mint_b",
            "symbol": "BETA",
            "name": "Beta Token",
            "pool": "pool_b",
            "dex": "Raydium",
            "quote": "SOL",
            "liquidity": 25000,
            "market_cap": 120000,
            "volume_5m": 8000,
            "holders": 120,
            "age": 90,
            "mint_disabled": True,
            "freeze_disabled": True,
            "liquidity_burned": True,
            "status": "active",
            "creator": "wallet_b",
            "signature": "tx_b",
            "timestamp": "2026-01-01T00:02:00Z",
        },
        {
            "mint": "mint_bad",
            "symbol": "BAD",
            "pool": "pool_bad",
            "liquidity": 100,
            "age": 900,
            "mint_disabled": False,
            "freeze_disabled": False,
            "liquidity_burned": False,
            "status": "active",
        },
    ]

    ledger = SolanaLaunchDiscoveryReplayLedger()
    caps = ledger.capabilities()
    health = ledger.health()

    baseline = ledger.run_discovery_and_record(
        raw_records,
        source_name="sld_008_test_source",
        min_liquidity_usd=1000,
        max_age_seconds=600,
        min_launch_score=0.55,
    )
    replay = ledger.run_discovery_and_record(
        list(reversed(raw_records)),
        source_name="sld_008_test_source",
        min_liquidity_usd=1000,
        max_age_seconds=600,
        min_launch_score=0.55,
    )
    comparison = ledger.compare(baseline, replay)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["snipe_allowed"] is False
    assert caps["deterministic"] is True
    assert caps["canonicalizes_volatile_fields"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert baseline.schema_version == "SLD-008"
    assert baseline.ledger_id == "oracle.discovery.ledger.solana_launch_replay"
    assert baseline.status == "passed"
    assert baseline.read_only is True
    assert len(baseline.entries) == 2

    assert baseline.run_fingerprint == replay.run_fingerprint
    assert comparison.matching is True
    assert comparison.status == "matched"
    assert comparison.read_only is True

    first = baseline.entries[0]
    assert first.read_only is True
    assert first.replay_status == "recorded"
    assert first.packet_fingerprint
    assert first.payload_fingerprint
    assert first.audit_fingerprint
    assert first.payload_summary["validation_required"] is True
    assert first.payload_summary["ranking_required"] is True
    assert first.payload_summary["registry_required"] is True
    assert first.payload_summary["execution_allowed"] is False
    assert first.payload_summary["signing_allowed"] is False
    assert first.payload_summary["fund_movement_allowed"] is False
    assert first.payload_summary["swap_allowed"] is False
    assert first.payload_summary["snipe_allowed"] is False
    assert first.payload_summary["read_only"] is True

    try:
        first.payload_summary["execution_allowed"] = True
        raise AssertionError("payload summary should be immutable")
    except TypeError:
        pass

    d = baseline.to_dict()
    c = comparison.to_dict()

    assert d["schema_version"] == "SLD-008"
    assert d["read_only"] is True
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["entries_emitted"] == 2
    assert "created_at" in d["telemetry"]["volatile_fields_excluded"]
    assert "detected_at" in d["telemetry"]["volatile_fields_excluded"]
    assert c["matching"] is True
    assert c["baseline_entries"] == 2
    assert c["replay_entries"] == 2

    print("[PASS] SLD-008 Solana Launch Discovery Replay Ledger")
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
    test_sld_008_solana_launch_discovery_replay_ledger()
'''

INIT_EXPORT = '''
try:
    from .solana_launch_discovery_replay_ledger import (
        SolanaLaunchDiscoveryReplayLedger,
        SolanaLaunchReplayLedgerEntry,
        SolanaLaunchReplayLedgerReport,
        SolanaLaunchReplayComparisonReport,
    )
except Exception:
    pass
'''

LEDGER_FILE.write_text(LEDGER_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "SolanaLaunchDiscoveryReplayLedger" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SLD-008 INSTALLER")
print(" Solana Launch Discovery Replay Ledger")
print("========================================")
print(f"[OK] Wrote {LEDGER_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] SLD-008 installed")
print()
print("Run:")
print("py test_sld_008_solana_launch_discovery_replay_ledger.py")