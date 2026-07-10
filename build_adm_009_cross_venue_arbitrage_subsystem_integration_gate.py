from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "arbitrage_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

GATE_FILE = MODULE_DIR / "cross_venue_arbitrage_subsystem_integration_gate.py"
TEST_FILE = ROOT / "test_adm_009_cross_venue_arbitrage_subsystem_integration_gate.py"
INIT_FILE = MODULE_DIR / "__init__.py"

GATE_CODE = r'''"""
ADM-009 Cross-Venue Arbitrage Subsystem Integration Gate

Full read-only integration gate for Cross-Venue Arbitrage Discovery Division.

Verifies:
- ADM-001 Arbitrage Discovery Contract
- ADM-002 Cross-Venue Source Adapter
- ADM-003 Discovery Engine
- ADM-004 Pipeline Gate
- ADM-005 Registry Bridge
- ADM-006 Pipeline Bridge
- ADM-007 OOS Runtime Gate
- ADM-008 Replay Ledger

Oracle remains read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .arbitrage_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    ArbitrageDiscoveryFamily,
    ArbitrageDiscoveryRequest,
)
from .cross_venue_arbitrage_source_adapter import CrossVenueArbitrageSourceAdapter
from .cross_venue_arbitrage_discovery_engine import CrossVenueArbitrageDiscoveryEngine
from .cross_venue_arbitrage_discovery_pipeline_gate import CrossVenueArbitrageDiscoveryPipelineGate
from .cross_venue_arbitrage_discovery_registry_bridge import CrossVenueArbitrageDiscoveryRegistryBridge
from .cross_venue_arbitrage_discovery_pipeline_bridge import CrossVenueArbitrageDiscoveryPipelineBridge
from .cross_venue_arbitrage_discovery_oos_runtime_gate import CrossVenueArbitrageDiscoveryOOSRuntimeGate
from .cross_venue_arbitrage_discovery_replay_ledger import CrossVenueArbitrageDiscoveryReplayLedger


SCHEMA_VERSION = "ADM-009"
GATE_ID = "oracle.discovery.gate.cross_venue_arbitrage_subsystem_integration"
GATE_NAME = "Cross-Venue Arbitrage Subsystem Integration Gate"


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
class CrossVenueArbitrageSubsystemIntegrationReport:
    schema_version: str
    gate_id: str
    status: str
    passed_checks: int
    failed_checks: int
    warning_count: int
    checks: Mapping[str, bool]
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
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class CrossVenueArbitrageSubsystemIntegrationGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "cross_venue_arbitrage_subsystem_gate_source",
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
                "ADM-001 contract",
                "ADM-002 source adapter",
                "ADM-003 discovery engine",
                "ADM-004 pipeline gate",
                "ADM-005 registry bridge",
                "ADM-006 pipeline bridge",
                "ADM-007 OOS runtime gate",
                "ADM-008 replay ledger",
                "deterministic replay",
                "immutable payloads",
                "no execution authority",
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

    def run(self, raw_records: Sequence[Any] | None = None) -> CrossVenueArbitrageSubsystemIntegrationReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = CrossVenueArbitrageSourceAdapter(source_name=self.source_name)
        batch = adapter.normalize_batch(raw)

        request = ArbitrageDiscoveryRequest(
            request_id="adm009.cross.venue.arbitrage.subsystem.integration",
            family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
            source_name=self.source_name,
            symbols=tuple(sorted({s.symbol for s in batch.snapshots})),
            venues=tuple(sorted({s.venue for s in batch.snapshots})),
            metadata={"snapshots": batch.snapshots},
        )

        engine = CrossVenueArbitrageDiscoveryEngine(
            min_net_edge_percent=self.min_net_edge_percent,
            min_liquidity=self.min_liquidity,
        )
        discovery_report = engine.discover(request)

        pipeline_gate = CrossVenueArbitrageDiscoveryPipelineGate(
            source_name=self.source_name,
            min_net_edge_percent=self.min_net_edge_percent,
            min_liquidity=self.min_liquidity,
        )
        pipeline_gate_report = pipeline_gate.run(raw)

        registry_bridge = CrossVenueArbitrageDiscoveryRegistryBridge()
        registry_report = registry_bridge.bridge_report(discovery_report)

        pipeline_bridge = CrossVenueArbitrageDiscoveryPipelineBridge()
        pipeline_report = pipeline_bridge.bridge_records(registry_report.records)

        oos_gate = CrossVenueArbitrageDiscoveryOOSRuntimeGate(
            source_name=self.source_name,
            min_net_edge_percent=self.min_net_edge_percent,
            min_liquidity=self.min_liquidity,
        )
        oos_report = oos_gate.run(raw)

        replay_ledger = CrossVenueArbitrageDiscoveryReplayLedger()
        replay_a = replay_ledger.record_packets(oos_report.packets)
        replay_b = replay_ledger.record_packets(oos_gate.run(tuple(reversed(raw))).packets)
        replay_compare = replay_ledger.compare(replay_a, replay_b)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "contract_schema_ok": CONTRACT_SCHEMA_VERSION == "ADM-001",
            "request_is_read_only": request.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "pipeline_gate_is_read_only": pipeline_gate.read_only is True,
            "registry_bridge_is_read_only": registry_bridge.read_only is True,
            "pipeline_bridge_is_read_only": pipeline_bridge.read_only is True,
            "oos_gate_is_read_only": oos_gate.read_only is True,
            "replay_ledger_is_read_only": replay_ledger.read_only is True,

            "adapter_schema_ok": batch.schema_version == "ADM-002",
            "engine_contract_schema_ok": discovery_report.schema_version == "ADM-001",
            "pipeline_gate_schema_ok": pipeline_gate_report.schema_version == "ADM-004",
            "registry_bridge_schema_ok": registry_report.schema_version == "ADM-005",
            "pipeline_bridge_schema_ok": pipeline_report.schema_version == "ADM-006",
            "oos_gate_schema_ok": oos_report.schema_version == "ADM-007",
            "replay_ledger_schema_ok": replay_a.schema_version == "ADM-008",

            "snapshots_emitted": len(batch.snapshots) == len(raw),
            "pairs_evaluated": discovery_report.telemetry.pairs_evaluated == 2,
            "opportunities_emitted": len(discovery_report.opportunities) == 1,
            "registry_records_emitted": len(registry_report.records) == 1,
            "pipeline_packets_emitted": len(pipeline_report.packets) == 1,
            "oos_packets_emitted": len(oos_report.packets) == 1,
            "replay_entries_emitted": len(replay_a.entries) == 1,

            "pipeline_gate_passed": pipeline_gate_report.status == "passed",
            "registry_bridge_passed": registry_report.status == "passed",
            "pipeline_bridge_passed": pipeline_report.status == "passed",
            "oos_gate_passed": oos_report.status == "passed",
            "replay_ledger_passed": replay_a.status == "passed",
            "replay_comparison_matched": replay_compare.matching is True,

            "all_opportunities_read_only": all(o.read_only is True for o in discovery_report.opportunities),
            "all_registry_records_read_only": all(r.read_only is True for r in registry_report.records),
            "all_pipeline_packets_read_only": all(p.read_only is True for p in pipeline_report.packets),
            "all_oos_packets_read_only": all(p.read_only is True for p in oos_report.packets),
            "all_replay_entries_read_only": all(e.read_only is True for e in replay_a.entries),

            "all_arbitrage_markets_shape": all(
                o.universal_market.get("market_type") == "cross_venue_arbitrage"
                and o.universal_market.get("execution_allowed") is False
                for o in discovery_report.opportunities
            ),
            "all_pipeline_packets_validation_ready": all(
                p.payload.get("validation_required") is True for p in pipeline_report.packets
            ),
            "all_pipeline_packets_registry_ready": all(
                p.payload.get("registry_required") is True for p in pipeline_report.packets
            ),
            "all_pipeline_packets_ranking_ready": all(
                p.payload.get("ranking_required") is True for p in pipeline_report.packets
            ),
            "execution_not_allowed": all(
                p.payload.get("execution_allowed") is False for p in pipeline_report.packets
            ),
            "order_not_allowed": all(
                p.payload.get("order_allowed") is False for p in pipeline_report.packets
            ),
            "route_not_allowed": all(
                p.payload.get("route_allowed") is False for p in pipeline_report.packets
            ),
            "leg_execution_not_allowed": all(
                p.payload.get("leg_execution_allowed") is False for p in pipeline_report.packets
            ),
            "no_execution_fields_in_registry": all(
                r.audit.get("execution_fields_present") is False for r in registry_report.records
            ),
            "no_execution_fields_in_pipeline": all(
                p.audit.get("execution_fields_present") is False for p in pipeline_report.packets
            ),

            "immutable_registry_payload": self._immutable_mapping_check(
                registry_report.records[0].payload if registry_report.records else {}
            ),
            "immutable_pipeline_payload": self._immutable_mapping_check(
                pipeline_report.packets[0].payload if pipeline_report.packets else {}
            ),
            "immutable_replay_summary": self._immutable_mapping_check(
                replay_a.entries[0].payload_summary if replay_a.entries else {}
            ),

            "telemetry_present_adapter": bool(batch.telemetry),
            "telemetry_present_engine": bool(discovery_report.telemetry),
            "telemetry_present_pipeline_gate": bool(pipeline_gate_report.telemetry),
            "telemetry_present_registry": bool(registry_report.telemetry),
            "telemetry_present_pipeline": bool(pipeline_report.telemetry),
            "telemetry_present_oos_gate": bool(oos_report.telemetry),
            "telemetry_present_replay": bool(replay_a.telemetry),

            "deterministic_replay_fingerprint": replay_a.run_fingerprint == replay_b.run_fingerprint,
            "read_only_telemetry_all": all(
                item.get("read_only") is True
                for item in (
                    batch.telemetry,
                    discovery_report.telemetry.to_dict(),
                    pipeline_gate_report.telemetry,
                    registry_report.telemetry,
                    pipeline_report.telemetry,
                    oos_report.telemetry,
                    replay_a.telemetry,
                )
            ),
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
                "snapshots_emitted": len(batch.snapshots),
                "pairs_evaluated": discovery_report.telemetry.pairs_evaluated,
                "opportunities_emitted": len(discovery_report.opportunities),
                "registry_records_emitted": len(registry_report.records),
                "pipeline_packets_emitted": len(pipeline_report.packets),
                "oos_packets_emitted": len(oos_report.packets),
                "replay_entries_emitted": len(replay_a.entries),
                "passed_checks": passed,
                "failed_checks": failed,
                "warning_count": 0,
                "read_only": True,
                "execution_allowed": False,
                "order_allowed": False,
                "route_allowed": False,
                "leg_execution_allowed": False,
                "replay_match": replay_compare.matching,
                "run_fingerprint": replay_a.run_fingerprint,
            }
        )

        return CrossVenueArbitrageSubsystemIntegrationReport(
            schema_version=self.schema_version,
            gate_id=self.gate_id,
            status="passed" if failed == 0 else "failed",
            passed_checks=passed,
            failed_checks=failed,
            warning_count=0,
            checks=_freeze(checks),
            telemetry=telemetry,
            read_only=True,
        )

    def _immutable_mapping_check(self, mapping: Any) -> bool:
        try:
            mapping["__mutation_test__"] = True
            return False
        except TypeError:
            return True
        except Exception:
            return False

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
    "CrossVenueArbitrageSubsystemIntegrationReport",
    "CrossVenueArbitrageSubsystemIntegrationGate",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_subsystem_integration_gate import (
    CrossVenueArbitrageSubsystemIntegrationGate,
)


def test_adm_009_cross_venue_arbitrage_subsystem_integration_gate():
    gate = CrossVenueArbitrageSubsystemIntegrationGate(
        source_name="adm_009_test_source",
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

    assert report.schema_version == "ADM-009"
    assert report.gate_id == "oracle.discovery.gate.cross_venue_arbitrage_subsystem_integration"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True

    assert report.checks["contract_schema_ok"] is True
    assert report.checks["adapter_schema_ok"] is True
    assert report.checks["engine_contract_schema_ok"] is True
    assert report.checks["pipeline_gate_schema_ok"] is True
    assert report.checks["registry_bridge_schema_ok"] is True
    assert report.checks["pipeline_bridge_schema_ok"] is True
    assert report.checks["oos_gate_schema_ok"] is True
    assert report.checks["replay_ledger_schema_ok"] is True

    assert report.checks["opportunities_emitted"] is True
    assert report.checks["registry_records_emitted"] is True
    assert report.checks["pipeline_packets_emitted"] is True
    assert report.checks["oos_packets_emitted"] is True
    assert report.checks["replay_entries_emitted"] is True

    assert report.checks["execution_not_allowed"] is True
    assert report.checks["order_not_allowed"] is True
    assert report.checks["route_not_allowed"] is True
    assert report.checks["leg_execution_not_allowed"] is True
    assert report.checks["deterministic_replay_fingerprint"] is True
    assert report.checks["immutable_registry_payload"] is True
    assert report.checks["immutable_pipeline_payload"] is True
    assert report.checks["immutable_replay_summary"] is True
    assert report.checks["read_only_telemetry_all"] is True

    d = report.to_dict()
    assert d["schema_version"] == "ADM-009"
    assert d["status"] == "passed"
    assert d["telemetry"]["opportunities_emitted"] == 1
    assert d["telemetry"]["registry_records_emitted"] == 1
    assert d["telemetry"]["pipeline_packets_emitted"] == 1
    assert d["telemetry"]["oos_packets_emitted"] == 1
    assert d["telemetry"]["replay_entries_emitted"] == 1
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["order_allowed"] is False
    assert d["telemetry"]["route_allowed"] is False
    assert d["telemetry"]["leg_execution_allowed"] is False
    assert d["telemetry"]["replay_match"] is True
    assert d["read_only"] is True

    print("[PASS] ADM-009 Cross-Venue Arbitrage Subsystem Integration Gate")
    print(
        {
            "schema_version": d["schema_version"],
            "gate_id": d["gate_id"],
            "status": d["status"],
            "passed_checks": d["passed_checks"],
            "failed_checks": d["failed_checks"],
            "opportunities": d["telemetry"]["opportunities_emitted"],
            "packets": d["telemetry"]["pipeline_packets_emitted"],
            "replay_match": d["telemetry"]["replay_match"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_adm_009_cross_venue_arbitrage_subsystem_integration_gate()
'''

INIT_EXPORT = '''
try:
    from .cross_venue_arbitrage_subsystem_integration_gate import (
        CrossVenueArbitrageSubsystemIntegrationGate,
        CrossVenueArbitrageSubsystemIntegrationReport,
    )
except Exception:
    pass
'''

GATE_FILE.write_text(GATE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "CrossVenueArbitrageSubsystemIntegrationGate" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ADM-009 INSTALLER")
print(" Cross-Venue Arbitrage Subsystem Integration Gate")
print("========================================")
print(f"[OK] Wrote {GATE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ADM-009 installed")
print()
print("Run:")
print("py test_adm_009_cross_venue_arbitrage_subsystem_integration_gate.py")