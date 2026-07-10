from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

GATE_FILE = MODULE_DIR / "prediction_market_discovery_oos_runtime_gate.py"
TEST_FILE = ROOT / "test_odm_007_prediction_market_discovery_oos_runtime_gate.py"
INIT_FILE = MODULE_DIR / "__init__.py"

GATE_CODE = r'''"""
ODM-007 Prediction Market Discovery OOS Runtime Gate

Read-only runtime gate proving the ODM prediction-market discovery chain can
produce OOS-ready pipeline packets without execution behavior.

Flow:
ODM-003 Source Adapter
 -> ODM-002 Discovery Engine
 -> ODM-005 Registry Bridge
 -> ODM-006 Pipeline Bridge
 -> ODM-007 OOS Runtime Gate

Oracle remains read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .prediction_market_discovery_pipeline_bridge import (
    PredictionMarketDiscoveryPipelineBridge,
)


SCHEMA_VERSION = "ODM-007"
GATE_ID = "oracle.discovery.gate.prediction_market_oos_runtime"
GATE_NAME = "Prediction Market Discovery OOS Runtime Gate"


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
class PredictionMarketOOSRuntimeGateReport:
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


class PredictionMarketDiscoveryOOSRuntimeGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "prediction_market_oos_runtime_gate_source",
        min_edge: float = 0.02,
        min_liquidity: float = 100.0,
    ) -> None:
        self.source_name = source_name
        self.min_edge = float(min_edge)
        self.min_liquidity = float(min_liquidity)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "ODM source adapter",
                "ODM discovery engine",
                "ODM registry bridge",
                "ODM pipeline bridge",
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

    def run(self, raw_markets: Sequence[Any] | None = None) -> PredictionMarketOOSRuntimeGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_markets or self._fixture_markets())

        bridge = PredictionMarketDiscoveryPipelineBridge()

        report_a = bridge.discover_registry_and_bridge(
            raw,
            source_name=self.source_name,
            min_edge=self.min_edge,
            min_liquidity=self.min_liquidity,
        )
        report_b = bridge.discover_registry_and_bridge(
            tuple(reversed(raw)),
            source_name=self.source_name,
            min_edge=self.min_edge,
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
            "all_packets_have_market_id": all(bool(p.market_id) for p in packets_a),
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
            }
        )

        return PredictionMarketOOSRuntimeGateReport(
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

    def _fixture_markets(self) -> Tuple[Mapping[str, Any], ...]:
        return (
            {
                "ticker": "KX.ODM007.YES",
                "question": "Will ODM-007 fixture one resolve yes?",
                "platform": "kalshi",
                "category": "oracle_test",
                "price": 40,
                "model_probability": 54,
                "liquidity": 2500,
                "volume": 10000,
                "status": "open",
            },
            {
                "ticker": "KX.ODM007.NO",
                "question": "Will ODM-007 fixture two resolve yes?",
                "platform": "kalshi",
                "category": "oracle_test",
                "price": 76,
                "model_probability": 64,
                "liquidity": 3000,
                "volume": 15000,
                "status": "open",
            },
            {
                "ticker": "KX.ODM007.REJECT",
                "question": "Will ODM-007 low-edge fixture resolve yes?",
                "platform": "kalshi",
                "category": "oracle_test",
                "price": 50,
                "model_probability": 50.5,
                "liquidity": 3000,
                "volume": 15000,
                "status": "open",
            },
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "PredictionMarketOOSRuntimeGateReport",
    "PredictionMarketDiscoveryOOSRuntimeGate",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_oos_runtime_gate import (
    PredictionMarketDiscoveryOOSRuntimeGate,
)


def test_odm_007_prediction_market_discovery_oos_runtime_gate():
    gate = PredictionMarketDiscoveryOOSRuntimeGate(
        source_name="odm_007_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "ODM-007"
    assert report.gate_id == "oracle.discovery.gate.prediction_market_oos_runtime"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True
    assert len(report.packets) == 2

    assert report.checks["gate_is_read_only"] is True
    assert report.checks["pipeline_bridge_is_read_only"] is True
    assert report.checks["deterministic_replay"] is True
    assert report.checks["all_packets_validation_required"] is True
    assert report.checks["all_packets_ranking_required"] is True
    assert report.checks["all_packets_registry_required"] is True
    assert report.checks["execution_not_allowed"] is True
    assert report.checks["immutable_packet_payload"] is True

    first = report.packets[0]
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["read_only"] is True
    assert first.audit["oracle_read_only"] is True
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    d = report.to_dict()
    assert d["schema_version"] == "ODM-007"
    assert d["status"] == "passed"
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["oos_validation_ready"] is True
    assert d["telemetry"]["oos_registry_ready"] is True
    assert d["telemetry"]["oos_ranking_ready"] is True
    assert d["telemetry"]["oos_pipeline_ready"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] ODM-007 Prediction Market Discovery OOS Runtime Gate")
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
    test_odm_007_prediction_market_discovery_oos_runtime_gate()
'''

INIT_EXPORT = '''
try:
    from .prediction_market_discovery_oos_runtime_gate import (
        PredictionMarketDiscoveryOOSRuntimeGate,
        PredictionMarketOOSRuntimeGateReport,
    )
except Exception:
    pass
'''

GATE_FILE.write_text(GATE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "PredictionMarketDiscoveryOOSRuntimeGate" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ODM-007 INSTALLER")
print(" Prediction Market Discovery OOS Runtime Gate")
print("========================================")
print(f"[OK] Wrote {GATE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] ODM-007 installed")
print()
print("Run:")
print("py test_odm_007_prediction_market_discovery_oos_runtime_gate.py")