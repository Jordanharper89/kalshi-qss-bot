"""
SLD-007 Solana Launch Discovery OOS Runtime Gate

Read-only runtime gate proving Solana launch discovery can produce
OOS-ready packets without signing, fund movement, swaps, sniping, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .solana_launch_discovery_pipeline_bridge import SolanaLaunchDiscoveryPipelineBridge


SCHEMA_VERSION = "SLD-007"
GATE_ID = "oracle.discovery.gate.solana_launch_oos_runtime"
GATE_NAME = "Solana Launch Discovery OOS Runtime Gate"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class SolanaLaunchOOSRuntimeGateReport:
    schema_version: str
    gate_id: str
    status: str
    passed_checks: int
    failed_checks: int
    warning_count: int
    checks: Mapping[str, bool]
    packets: Tuple[Any, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "status": self.status,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warning_count": self.warning_count,
            "checks": dict(self.checks),
            "packets": [
                p.to_dict() if hasattr(p, "to_dict") else dict(p)
                for p in self.packets
            ],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class SolanaLaunchDiscoveryOOSRuntimeGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "solana_launch_oos_runtime_gate_source",
        min_liquidity_usd: float = 1000.0,
        max_age_seconds: float = 600.0,
        min_launch_score: float = 0.55,
    ) -> None:
        self.source_name = str(source_name)
        self.min_liquidity_usd = float(min_liquidity_usd)
        self.max_age_seconds = float(max_age_seconds)
        self.min_launch_score = float(min_launch_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "SLD source adapter",
                "SLD discovery engine",
                "SLD registry bridge",
                "SLD pipeline bridge",
                "OOS validation readiness",
                "OOS registry readiness",
                "OOS ranking readiness",
                "OOS pipeline readiness",
                "deterministic replay",
                "no signing authority",
                "no fund movement authority",
                "no swap authority",
                "no snipe authority",
                "no execution authority",
            ],
            "compatible_with": [
                "OOS-001 Registry",
                "OOS-002 Ranking",
                "OOS-003 Pipeline",
                "OOS-004 Validation",
            ],
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
            "snipe_allowed": False,
            "deterministic": True,
            "telemetry": True,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def run(self, raw_records: Sequence[Any] | None = None) -> SolanaLaunchOOSRuntimeGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        bridge = SolanaLaunchDiscoveryPipelineBridge()

        report_a = bridge.discover_registry_and_bridge(
            raw,
            source_name=self.source_name,
            min_liquidity_usd=self.min_liquidity_usd,
            max_age_seconds=self.max_age_seconds,
            min_launch_score=self.min_launch_score,
        )
        report_b = bridge.discover_registry_and_bridge(
            tuple(reversed(raw)),
            source_name=self.source_name,
            min_liquidity_usd=self.min_liquidity_usd,
            max_age_seconds=self.max_age_seconds,
            min_launch_score=self.min_launch_score,
        )

        packets_a = tuple(report_a.packets)
        packets_b = tuple(report_b.packets)
        packet_ids_a = tuple(p.packet_id for p in packets_a)
        packet_ids_b = tuple(p.packet_id for p in packets_b)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "pipeline_bridge_is_read_only": bridge.read_only is True,
            "pipeline_report_is_read_only": report_a.read_only is True,
            "packets_emitted": len(packets_a) == 2,
            "deterministic_replay": packet_ids_a == packet_ids_b,
            "all_packets_read_only": all(p.read_only is True for p in packets_a),
            "all_packets_pipeline_ready": all(p.pipeline_status == "pipeline_ready" for p in packets_a),
            "all_packets_have_packet_id": all(bool(p.packet_id) for p in packets_a),
            "all_packets_have_registry_key": all(bool(p.registry_key) for p in packets_a),
            "all_packets_have_opportunity_id": all(bool(p.opportunity_id) for p in packets_a),
            "all_packets_have_mint": all(bool(p.mint) for p in packets_a),
            "all_packets_have_symbol": all(bool(p.symbol) for p in packets_a),
            "all_packets_validation_required": all(
                p.payload.get("validation_required") is True for p in packets_a
            ),
            "all_packets_ranking_required": all(
                p.payload.get("ranking_required") is True for p in packets_a
            ),
            "all_packets_registry_required": all(
                p.payload.get("registry_required") is True for p in packets_a
            ),
            "execution_not_allowed": all(
                p.payload.get("execution_allowed") is False for p in packets_a
            ),
            "signing_not_allowed": all(
                p.payload.get("signing_allowed") is False for p in packets_a
            ),
            "fund_movement_not_allowed": all(
                p.payload.get("fund_movement_allowed") is False for p in packets_a
            ),
            "swap_not_allowed": all(
                p.payload.get("swap_allowed") is False for p in packets_a
            ),
            "snipe_not_allowed": all(
                p.payload.get("snipe_allowed") is False for p in packets_a
            ),
            "oos_payload_read_only": all(
                p.payload.get("read_only") is True for p in packets_a
            ),
            "registry_payload_present": all(
                bool(p.payload.get("registry_payload")) for p in packets_a
            ),
            "universal_market_present": all(
                bool(p.payload.get("registry_payload", {}).get("universal_market"))
                for p in packets_a
            ),
            "solana_launch_market_shape": all(
                p.payload.get("registry_payload", {}).get("universal_market", {}).get("market_type")
                == "solana_launch"
                for p in packets_a
            ),
            "explanation_present": all(
                bool(p.payload.get("registry_payload", {}).get("explanation"))
                for p in packets_a
            ),
            "telemetry_present": all(
                bool(p.payload.get("registry_payload", {}).get("telemetry"))
                for p in packets_a
            ),
            "source_engine_id_present": all(
                bool(p.payload.get("source_engine_id")) for p in packets_a
            ),
            "source_engine_id_solana_launch": all(
                p.payload.get("source_engine_id") == "oracle.discovery.solana_launch"
                for p in packets_a
            ),
            "audit_read_only": all(
                p.audit.get("oracle_read_only") is True for p in packets_a
            ),
            "audit_handoff_target_present": all(
                p.audit.get("handoff_target") == "OOS Opportunity Pipeline"
                for p in packets_a
            ),
            "no_execution_fields_present": all(
                p.audit.get("execution_fields_present") is False for p in packets_a
            ),
            "audit_execution_not_allowed": all(
                p.audit.get("execution_allowed") is False for p in packets_a
            ),
            "audit_signing_not_allowed": all(
                p.audit.get("signing_allowed") is False for p in packets_a
            ),
            "audit_fund_movement_not_allowed": all(
                p.audit.get("fund_movement_allowed") is False for p in packets_a
            ),
            "audit_swap_not_allowed": all(
                p.audit.get("swap_allowed") is False for p in packets_a
            ),
            "audit_snipe_not_allowed": all(
                p.audit.get("snipe_allowed") is False for p in packets_a
            ),
            "immutable_packet_payload": self._check_immutable_payload(packets_a),
        }

        passed = sum(1 for ok in checks.values() if ok)
        failed = sum(1 for ok in checks.values() if not ok)

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "gate_id": self.gate_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "raw_records_seen": len(raw),
                "packets_seen": len(packets_a),
                "passed_checks": passed,
                "failed_checks": failed,
                "warning_count": 0,
                "read_only": True,
                "deterministic_replay": packet_ids_a == packet_ids_b,
                "oos_validation_ready": checks["all_packets_validation_required"],
                "oos_registry_ready": checks["all_packets_registry_required"],
                "oos_ranking_ready": checks["all_packets_ranking_required"],
                "oos_pipeline_ready": checks["all_packets_pipeline_ready"],
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
            }
        )

        return SolanaLaunchOOSRuntimeGateReport(
            schema_version=self.schema_version,
            gate_id=self.gate_id,
            status="passed" if failed == 0 else "failed",
            passed_checks=passed,
            failed_checks=failed,
            warning_count=0,
            checks=_freeze(checks),
            packets=packets_a,
            telemetry=telemetry,
            read_only=True,
        )

    def _check_immutable_payload(self, packets: Tuple[Any, ...]) -> bool:
        if not packets:
            return False
        try:
            packets[0].payload["execution_allowed"] = True
            return False
        except TypeError:
            return True

    def _fixture_records(self) -> Tuple[Mapping[str, Any], ...]:
        return (
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
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "SolanaLaunchOOSRuntimeGateReport",
    "SolanaLaunchDiscoveryOOSRuntimeGate",
]
