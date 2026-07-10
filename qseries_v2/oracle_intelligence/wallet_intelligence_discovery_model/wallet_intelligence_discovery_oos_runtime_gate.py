"""
WDM-007 Wallet Intelligence Discovery OOS Runtime Gate

Read-only runtime gate proving the wallet intelligence discovery chain can
produce OOS-ready packets without signing, fund movement, swaps, or execution.

Flow:
WDM-002 Source Adapter
 -> WDM-003 Discovery Engine
 -> WDM-005 Registry Bridge
 -> WDM-006 Pipeline Bridge
 -> WDM-007 OOS Runtime Gate
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .wallet_intelligence_discovery_pipeline_bridge import (
    WalletIntelligenceDiscoveryPipelineBridge,
)


SCHEMA_VERSION = "WDM-007"
GATE_ID = "oracle.discovery.gate.wallet_intelligence_oos_runtime"
GATE_NAME = "Wallet Intelligence Discovery OOS Runtime Gate"


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
class WalletIntelligenceOOSRuntimeGateReport:
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


class WalletIntelligenceDiscoveryOOSRuntimeGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "wallet_intelligence_oos_runtime_gate_source",
        min_wallet_score: float = 0.70,
        min_usd_value: float = 1000.0,
        min_signal_score: float = 0.55,
    ) -> None:
        self.source_name = str(source_name)
        self.min_wallet_score = float(min_wallet_score)
        self.min_usd_value = float(min_usd_value)
        self.min_signal_score = float(min_signal_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "WDM source adapter",
                "WDM discovery engine",
                "WDM registry bridge",
                "WDM pipeline bridge",
                "OOS validation readiness",
                "OOS registry readiness",
                "OOS ranking readiness",
                "OOS pipeline readiness",
                "deterministic replay",
                "no signing authority",
                "no fund movement authority",
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

    def run(self, raw_records: Sequence[Any] | None = None) -> WalletIntelligenceOOSRuntimeGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        bridge = WalletIntelligenceDiscoveryPipelineBridge()

        report_a = bridge.discover_registry_and_bridge(
            raw,
            source_name=self.source_name,
            min_wallet_score=self.min_wallet_score,
            min_usd_value=self.min_usd_value,
            min_signal_score=self.min_signal_score,
        )
        report_b = bridge.discover_registry_and_bridge(
            tuple(reversed(raw)),
            source_name=self.source_name,
            min_wallet_score=self.min_wallet_score,
            min_usd_value=self.min_usd_value,
            min_signal_score=self.min_signal_score,
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
            "all_packets_have_wallet": all(bool(p.wallet) for p in packets_a),
            "all_packets_have_chain": all(bool(p.chain) for p in packets_a),
            "all_packets_have_symbol": all(bool(p.symbol) for p in packets_a),
            "all_packets_have_signal_type": all(bool(p.signal_type) for p in packets_a),
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
            "wallet_intelligence_market_shape": all(
                p.payload.get("registry_payload", {}).get("universal_market", {}).get("market_type")
                == "wallet_intelligence"
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
            "source_engine_id_wallet_intelligence": all(
                p.payload.get("source_engine_id") == "oracle.discovery.wallet_intelligence"
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
            }
        )

        return WalletIntelligenceOOSRuntimeGateReport(
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
                "address": "wallet_a",
                "network": "solana",
                "token_symbol": "WIF",
                "token_address": "wif_mint",
                "type": "accumulate",
                "token_amount": 25000,
                "value_usd": 10000,
                "token_price": 0.40,
                "tx_hash": "tx_a",
                "block_time": "2026-01-01T00:01:00Z",
                "wallet_score": 0.93,
                "realized_pnl": 25000,
                "win_rate": 0.81,
                "holding_count": 8,
            },
            {
                "wallet": "wallet_b",
                "chain": "Solana",
                "symbol": "BONK",
                "mint": "bonk_mint",
                "action": "buy",
                "amount": 1000000,
                "usd_value": 5000,
                "price": 0.005,
                "signature": "tx_b",
                "timestamp": "2026-01-01T00:02:00Z",
                "smart_money_score": 0.88,
                "pnl": 12000,
                "win_rate": 0.72,
                "positions": 15,
            },
            {
                "wallet": "wallet_c",
                "chain": "solana",
                "symbol": "LOW",
                "mint": "low_mint",
                "action": "buy",
                "amount": 100,
                "usd_value": 100,
                "price": 1.0,
                "signature": "tx_c",
                "timestamp": "2026-01-01T00:03:00Z",
                "smart_money_score": 0.20,
                "pnl": 0,
                "win_rate": 0.20,
                "positions": 1,
            },
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "WalletIntelligenceOOSRuntimeGateReport",
    "WalletIntelligenceDiscoveryOOSRuntimeGate",
]
