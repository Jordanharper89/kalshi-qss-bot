from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "crypto_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

GATE_FILE = MODULE_DIR / "crypto_spot_discovery_subsystem_integration_gate.py"
TEST_FILE = ROOT / "test_cdm_009_crypto_spot_discovery_subsystem_integration_gate.py"
INIT_FILE = MODULE_DIR / "__init__.py"

GATE_CODE = r'''"""
CDM-009 Crypto Spot Discovery Subsystem Integration Gate

Full read-only integration gate for Crypto Spot Discovery Division.

Verifies:
- CDM-001 Crypto Discovery Contract
- CDM-002 Crypto Spot Source Adapter
- CDM-003 Crypto Spot Discovery Engine
- CDM-004 Crypto Spot Pipeline Gate
- CDM-005 Crypto Spot Registry Bridge
- CDM-006 Crypto Spot Pipeline Bridge
- CDM-007 Crypto Spot OOS Runtime Gate
- CDM-008 Crypto Spot Replay Ledger

Oracle remains read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .crypto_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    CryptoDiscoveryFamily,
    CryptoDiscoveryRequest,
)
from .crypto_spot_source_adapter import CryptoSpotSourceAdapter
from .crypto_spot_discovery_engine import CryptoSpotDiscoveryEngine
from .crypto_spot_discovery_pipeline_gate import CryptoSpotDiscoveryPipelineGate
from .crypto_spot_discovery_registry_bridge import CryptoSpotDiscoveryRegistryBridge
from .crypto_spot_discovery_pipeline_bridge import CryptoSpotDiscoveryPipelineBridge
from .crypto_spot_discovery_oos_runtime_gate import CryptoSpotDiscoveryOOSRuntimeGate
from .crypto_spot_discovery_replay_ledger import CryptoSpotDiscoveryReplayLedger


SCHEMA_VERSION = "CDM-009"
GATE_ID = "oracle.discovery.gate.crypto_spot_subsystem_integration"
GATE_NAME = "Crypto Spot Discovery Subsystem Integration Gate"


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
class CryptoSpotSubsystemIntegrationReport:
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


class CryptoSpotDiscoverySubsystemIntegrationGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "crypto_spot_subsystem_gate_source",
        min_edge_percent: float = 0.01,
        min_liquidity: float = 1000.0,
    ) -> None:
        self.source_name = str(source_name)
        self.min_edge_percent = float(min_edge_percent)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "CDM-001 contract",
                "CDM-002 source adapter",
                "CDM-003 discovery engine",
                "CDM-004 pipeline gate",
                "CDM-005 registry bridge",
                "CDM-006 pipeline bridge",
                "CDM-007 OOS runtime gate",
                "CDM-008 replay ledger",
                "deterministic replay",
                "immutable payloads",
                "no execution authority",
            ],
            "execution": False,
            "swap_allowed": False,
            "order_allowed": False,
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

    def run(self, raw_records: Sequence[Any] | None = None) -> CryptoSpotSubsystemIntegrationReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = CryptoSpotSourceAdapter(source_name=self.source_name)
        batch = adapter.normalize_batch(raw)

        request = CryptoDiscoveryRequest(
            request_id="cdm009.crypto.spot.subsystem.integration",
            family=CryptoDiscoveryFamily.CRYPTO_SPOT,
            source_name=self.source_name,
            symbols=tuple(s.symbol for s in batch.snapshots),
            metadata={"snapshots": batch.snapshots},
        )

        engine = CryptoSpotDiscoveryEngine(
            min_edge_percent=self.min_edge_percent,
            min_liquidity=self.min_liquidity,
        )
        discovery_report = engine.discover(request)

        pipeline_gate = CryptoSpotDiscoveryPipelineGate(
            source_name=self.source_name,
            min_edge_percent=self.min_edge_percent,
            min_liquidity=self.min_liquidity,
        )
        pipeline_gate_report = pipeline_gate.run(raw)

        registry_bridge = CryptoSpotDiscoveryRegistryBridge()
        registry_report = registry_bridge.bridge_report(discovery_report)

        pipeline_bridge = CryptoSpotDiscoveryPipelineBridge()
        pipeline_report = pipeline_bridge.bridge_records(registry_report.records)

        oos_gate = CryptoSpotDiscoveryOOSRuntimeGate(
            source_name=self.source_name,
            min_edge_percent=self.min_edge_percent,
            min_liquidity=self.min_liquidity,
        )
        oos_report = oos_gate.run(raw)

        replay_ledger = CryptoSpotDiscoveryReplayLedger()
        replay_a = replay_ledger.record_packets(oos_report.packets)

        oos_report_reversed = oos_gate.run(tuple(reversed(raw)))
        replay_b = replay_ledger.record_packets(oos_report_reversed.packets)
        replay_compare = replay_ledger.compare(replay_a, replay_b)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "contract_schema_ok": CONTRACT_SCHEMA_VERSION == "CDM-001",
            "request_is_read_only": request.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "pipeline_gate_is_read_only": pipeline_gate.read_only is True,
            "registry_bridge_is_read_only": registry_bridge.read_only is True,
            "pipeline_bridge_is_read_only": pipeline_bridge.read_only is True,
            "oos_gate_is_read_only": oos_gate.read_only is True,
            "replay_ledger_is_read_only": replay_ledger.read_only is True,

            "adapter_schema_ok": batch.schema_version == "CDM-002",
            "engine_contract_schema_ok": discovery_report.schema_version == "CDM-001",
            "pipeline_gate_schema_ok": pipeline_gate_report.schema_version == "CDM-004",
            "registry_bridge_schema_ok": registry_report.schema_version == "CDM-005",
            "pipeline_bridge_schema_ok": pipeline_report.schema_version == "CDM-006",
            "oos_gate_schema_ok": oos_report.schema_version == "CDM-007",
            "replay_ledger_schema_ok": replay_a.schema_version == "CDM-008",

            "snapshots_emitted": len(batch.snapshots) == len(raw),
            "opportunities_emitted": len(discovery_report.opportunities) == 2,
            "registry_records_emitted": len(registry_report.records) == 2,
            "pipeline_packets_emitted": len(pipeline_report.packets) == 2,
            "oos_packets_emitted": len(oos_report.packets) == 2,
            "replay_entries_emitted": len(replay_a.entries) == 2,

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

            "all_crypto_markets_are_spot": all(
                o.universal_market.get("market_type") == "crypto_spot"
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
            "swap_not_allowed": all(
                p.payload.get("swap_allowed") is False for p in pipeline_report.packets
            ),
            "order_not_allowed": all(
                p.payload.get("order_allowed") is False for p in pipeline_report.packets
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
                "swap_allowed": False,
                "order_allowed": False,
                "replay_match": replay_compare.matching,
                "run_fingerprint": replay_a.run_fingerprint,
            }
        )

        return CryptoSpotSubsystemIntegrationReport(
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
                "exchange": "coinbase",
                "price": 65000,
                "fair_value": 67000,
                "bid": 64990,
                "ask": 65010,
                "volume": 5000000,
                "depth": 2500000,
                "volatility_24h": 0.03,
                "status": "active",
            },
            {
                "symbol": "ETH/USD",
                "exchange": "coinbase",
                "price": 3500,
                "model_price": 3400,
                "bid": 3499,
                "ask": 3501,
                "volume_24h": 1000000,
                "liquidity": 500000,
                "volatility": 0.04,
                "status": "active",
            },
            {
                "symbol": "SOL-USD",
                "exchange": "coinbase",
                "price": 150,
                "fair_value": 151,
                "volume": 1000000,
                "depth": 500000,
                "status": "active",
            },
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "CryptoSpotSubsystemIntegrationReport",
    "CryptoSpotDiscoverySubsystemIntegrationGate",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_discovery_subsystem_integration_gate import (
    CryptoSpotDiscoverySubsystemIntegrationGate,
)


def test_cdm_009_crypto_spot_discovery_subsystem_integration_gate():
    gate = CryptoSpotDiscoverySubsystemIntegrationGate(
        source_name="cdm_009_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["swap_allowed"] is False
    assert caps["order_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "CDM-009"
    assert report.gate_id == "oracle.discovery.gate.crypto_spot_subsystem_integration"
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
    assert report.checks["swap_not_allowed"] is True
    assert report.checks["order_not_allowed"] is True
    assert report.checks["deterministic_replay_fingerprint"] is True
    assert report.checks["immutable_registry_payload"] is True
    assert report.checks["immutable_pipeline_payload"] is True
    assert report.checks["immutable_replay_summary"] is True
    assert report.checks["read_only_telemetry_all"] is True

    d = report.to_dict()
    assert d["schema_version"] == "CDM-009"
    assert d["status"] == "passed"
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["registry_records_emitted"] == 2
    assert d["telemetry"]["pipeline_packets_emitted"] == 2
    assert d["telemetry"]["oos_packets_emitted"] == 2
    assert d["telemetry"]["replay_entries_emitted"] == 2
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["swap_allowed"] is False
    assert d["telemetry"]["order_allowed"] is False
    assert d["telemetry"]["replay_match"] is True
    assert d["read_only"] is True

    print("[PASS] CDM-009 Crypto Spot Discovery Subsystem Integration Gate")
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
    test_cdm_009_crypto_spot_discovery_subsystem_integration_gate()
'''

INIT_EXPORT = '''
try:
    from .crypto_spot_discovery_subsystem_integration_gate import (
        CryptoSpotDiscoverySubsystemIntegrationGate,
        CryptoSpotSubsystemIntegrationReport,
    )
except Exception:
    pass
'''

GATE_FILE.write_text(GATE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "CryptoSpotDiscoverySubsystemIntegrationGate" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" CDM-009 INSTALLER")
print(" Crypto Spot Discovery Subsystem Integration Gate")
print("========================================")
print(f"[OK] Wrote {GATE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] CDM-009 installed")
print()
print("Run:")
print("py test_cdm_009_crypto_spot_discovery_subsystem_integration_gate.py")