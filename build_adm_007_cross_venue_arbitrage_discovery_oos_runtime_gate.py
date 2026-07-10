from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "arbitrage_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

GATE_FILE = MODULE_DIR / "cross_venue_arbitrage_discovery_oos_runtime_gate.py"
TEST_FILE = ROOT / "test_adm_007_cross_venue_arbitrage_discovery_oos_runtime_gate.py"
INIT_FILE = MODULE_DIR / "__init__.py"

GATE_CODE = r'''"""
ADM-007 Cross-Venue Arbitrage Discovery OOS Runtime Gate

Read-only runtime gate proving the arbitrage discovery chain can produce
OOS-ready packets without execution behavior.

Flow:
ADM-002 Source Adapter
 -> ADM-003 Discovery Engine
 -> ADM-005 Registry Bridge
 -> ADM-006 Pipeline Bridge
 -> ADM-007 OOS Runtime Gate
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .cross_venue_arbitrage_discovery_pipeline_bridge import (
    CrossVenueArbitrageDiscoveryPipelineBridge,
)


SCHEMA_VERSION = "ADM-007"
GATE_ID = "oracle.discovery.gate.cross_venue_arbitrage_oos_runtime"
GATE_NAME = "Cross-Venue Arbitrage Discovery OOS Runtime Gate"


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
class CrossVenueArbitrageOOSRuntimeGateReport:
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


class CrossVenueArbitrageDiscoveryOOSRuntimeGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "cross_venue_arbitrage_oos_runtime_gate_source",
        min_net_edge_percent: float = 0.001,
        min_liquidity: float = 1000.0,
    ) -> None:
        self.source_name = str(source_name)
        self.min_net_edge_percent = float(min_net_edge_percent)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "ADM source adapter",
                "ADM discovery engine",
                "ADM registry bridge",
                "ADM pipeline bridge",
                "OOS validation readiness",
                "OOS registry readiness",
                "OOS ranking readiness",
                "OOS pipeline readiness",
                "deterministic replay",
                "no execution authority",
            ],
            "compatible_with": [
                "OOS-001 Registry",
                "OOS-002 Ranking",
                "OOS-003 Pipeline",
                "OOS-004 Validation",
            ],
            "execution": False,
            "order_allowed": False,
            "route_allowed": False,
            "leg_execution_allowed": False,
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

    def run(self, raw_records: Sequence[Any] | None = None) -> CrossVenueArbitrageOOSRuntimeGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        bridge = CrossVenueArbitrageDiscoveryPipelineBridge()

        report_a = bridge.discover_registry_and_bridge(
            raw,
            source_name=self.source_name,
            min_net_edge_percent=self.min_net_edge_percent,
            min_liquidity=self.min_liquidity,
        )
        report_b = bridge.discover_registry_and_bridge(
            tuple(reversed(raw)),
            source_name=self.source_name,
            min_net_edge_percent=self.min_net_edge_percent,
            min_liquidity=self.min_liquidity,
        )

        packets_a = tuple(report_a.packets)
        packets_b = tuple(report_b.packets)

        packet_ids_a = tuple(p.packet_id for p in packets_a)
        packet_ids_b = tuple(p.packet_id for p in packets_b)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "pipeline_bridge_is_read_only": bridge.read_only is True,
            "pipeline_report_is_read_only": report_a.read_only is True,
            "packets_emitted": len(packets_a) >= 1,
            "deterministic_replay": packet_ids_a == packet_ids_b,
            "all_packets_read_only": all(p.read_only is True for p in packets_a),
            "all_packets_pipeline_ready": all(p.pipeline_status == "pipeline_ready" for p in packets_a),
            "all_packets_have_packet_id": all(bool(p.packet_id) for p in packets_a),
            "all_packets_have_registry_key": all(bool(p.registry_key) for p in packets_a),
            "all_packets_have_opportunity_id": all(bool(p.opportunity_id) for p in packets_a),
            "all_packets_have_symbol": all(bool(p.symbol) for p in packets_a),
            "all_packets_have_buy_sell_venues": all(
                bool(p.buy_venue) and bool(p.sell_venue) and p.buy_venue != p.sell_venue
                for p in packets_a
            ),
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
            "order_not_allowed": all(
                p.payload.get("order_allowed") is False for p in packets_a
            ),
            "route_not_allowed": all(
                p.payload.get("route_allowed") is False for p in packets_a
            ),
            "leg_execution_not_allowed": all(
                p.payload.get("leg_execution_allowed") is False for p in packets_a
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
            "arbitrage_market_shape": all(
                p.payload.get("registry_payload", {}).get("universal_market", {}).get("market_type")
                == "cross_venue_arbitrage"
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
            "source_engine_id_arbitrage": all(
                p.payload.get("source_engine_id") == "oracle.discovery.cross_venue_arbitrage"
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
                "order_allowed": False,
                "route_allowed": False,
                "leg_execution_allowed": False,
            }
        )

        return CrossVenueArbitrageOOSRuntimeGateReport(
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
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "CrossVenueArbitrageOOSRuntimeGateReport",
    "CrossVenueArbitrageDiscoveryOOSRuntimeGate",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_discovery_oos_runtime_gate import (
    CrossVenueArbitrageDiscoveryOOSRuntimeGate,
)


def test_adm_007_cross_venue_arbitrage_discovery_oos_runtime_gate():
    gate = CrossVenueArbitrageDiscoveryOOSRuntimeGate(
        source_name="adm_007_test_source",
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["route_allowed"] is False
    assert caps["leg_execution_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "ADM-007"
    assert report.gate_id == "oracle.discovery.gate.cross_venue_arbitrage_oos_runtime"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True
    assert len(report.packets) == 1

    assert report.checks["gate_is_read_only"] is True
    assert report.checks["pipeline_bridge_is_read_only"] is True
    assert report.checks["deterministic_replay"] is True
    assert report.checks["all_packets_validation_required"] is True
    assert report.checks["all_packets_ranking_required"] is True
    assert report.checks["all_packets_registry_required"] is True
    assert report.checks["execution_not_allowed"] is True
    assert report.checks["order_not_allowed"] is True
    assert report.checks["route_not_allowed"] is True
    assert report.checks["leg_execution_not_allowed"] is True
    assert report.checks["arbitrage_market_shape"] is True
    assert report.checks["source_engine_id_arbitrage"] is True
    assert report.checks["immutable_packet_payload"] is True

    first = report.packets[0]
    assert first.symbol == "BTC-USD"
    assert first.buy_venue == "coinbase"
    assert first.sell_venue == "kraken"
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["route_allowed"] is False
    assert first.payload["leg_execution_allowed"] is False
    assert first.payload["read_only"] is True
    assert first.audit["oracle_read_only"] is True
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    d = report.to_dict()
    assert d["schema_version"] == "ADM-007"
    assert d["status"] == "passed"
    assert d["telemetry"]["packets_seen"] == 1
    assert d["telemetry"]["oos_validation_ready"] is True
    assert d["telemetry"]["oos_registry_ready"] is True
    assert d["telemetry"]["oos_ranking_ready"] is True
    assert d["telemetry"]["oos_pipeline_ready"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["order_allowed"] is False
    assert d["telemetry"]["route_allowed"] is False
    assert d["telemetry"]["leg_execution_allowed"] is False

    print("[PASS] ADM-007 Cross-Venue Arbitrage Discovery OOS Runtime Gate")
    print(
        {
            "schema_version": d["schema_version"],
            "gate_id": d["gate_id"],
            "status": d["status"],
            "passed_checks": d["passed_checks"],
            "failed_checks": d["failed_checks"],
            "packets": len(d["packets"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_adm_007_cross_venue_arbitrage_discovery_oos_runtime_gate()
'''

INIT_EXPORT = '''
try:
    from .cross_venue_arbitrage_discovery_oos_runtime_gate import (
        CrossVenueArbitrageDiscoveryOOSRuntimeGate,
        CrossVenueArbitrageOOSRuntimeGateReport,
    )
except Exception:
    pass
'''

GATE_FILE.write_text(GATE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "CrossVenueArbitrageDiscoveryOOSRuntimeGate" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ADM-007 INSTALLER")
print(" Cross-Venue Arbitrage Discovery OOS Runtime Gate")
print("========================================")
print(f"[OK] Wrote {GATE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ADM-007 installed")
print()
print("Run:")
print("py test_adm_007_cross_venue_arbitrage_discovery_oos_runtime_gate.py")