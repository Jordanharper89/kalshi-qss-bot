from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "social_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

GATE_FILE = MODULE_DIR / "social_intelligence_discovery_oos_runtime_gate.py"
TEST_FILE = ROOT / "test_sid_007_social_intelligence_discovery_oos_runtime_gate.py"
INIT_FILE = MODULE_DIR / "__init__.py"

GATE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .social_intelligence_discovery_pipeline_bridge import SocialIntelligenceDiscoveryPipelineBridge

SCHEMA_VERSION = "SID-007"
GATE_ID = "oracle.discovery.gate.social_intelligence_oos_runtime"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(v: Any) -> Any:
    if isinstance(v, Mapping):
        return MappingProxyType({str(k): _freeze(x) for k, x in v.items()})
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, tuple):
        return tuple(_freeze(x) for x in v)
    return v


@dataclass(frozen=True)
class SocialIntelligenceOOSRuntimeGateReport:
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
            "packets": [p.to_dict() if hasattr(p, "to_dict") else dict(p) for p in self.packets],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class SocialIntelligenceDiscoveryOOSRuntimeGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    read_only = True

    def __init__(self, source_name: str = "social_intelligence_oos_runtime_gate_source", min_social_score: float = 0.55) -> None:
        self.source_name = str(source_name)
        self.min_social_score = float(min_social_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "read_only": True,
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "broker_connectivity_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
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

    def run(self, raw_records: Sequence[Any] | None = None) -> SocialIntelligenceOOSRuntimeGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        bridge = SocialIntelligenceDiscoveryPipelineBridge()
        report_a = bridge.discover_registry_and_bridge(raw, source_name=self.source_name, min_social_score=self.min_social_score)
        report_b = bridge.discover_registry_and_bridge(tuple(reversed(raw)), source_name=self.source_name, min_social_score=self.min_social_score)

        packets_a = tuple(report_a.packets)
        packets_b = tuple(report_b.packets)
        ids_a = tuple(p.packet_id for p in packets_a)
        ids_b = tuple(p.packet_id for p in packets_b)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "pipeline_bridge_is_read_only": bridge.read_only is True,
            "pipeline_report_is_read_only": report_a.read_only is True,
            "packets_emitted": len(packets_a) == 2,
            "deterministic_replay": ids_a == ids_b,
            "all_packets_read_only": all(p.read_only is True for p in packets_a),
            "all_packets_pipeline_ready": all(p.pipeline_status == "pipeline_ready" for p in packets_a),
            "all_packets_have_packet_id": all(bool(p.packet_id) for p in packets_a),
            "all_packets_have_registry_key": all(bool(p.registry_key) for p in packets_a),
            "all_packets_have_opportunity_id": all(bool(p.opportunity_id) for p in packets_a),
            "all_packets_have_post_id": all(bool(p.post_id) for p in packets_a),
            "all_packets_have_topic": all(bool(p.topic) for p in packets_a),
            "all_packets_have_platform": all(bool(p.platform) for p in packets_a),
            "all_packets_validation_required": all(p.payload.get("validation_required") is True for p in packets_a),
            "all_packets_ranking_required": all(p.payload.get("ranking_required") is True for p in packets_a),
            "all_packets_registry_required": all(p.payload.get("registry_required") is True for p in packets_a),
            "execution_not_allowed": all(p.payload.get("execution_allowed") is False for p in packets_a),
            "order_not_allowed": all(p.payload.get("order_allowed") is False for p in packets_a),
            "position_sizing_not_allowed": all(p.payload.get("position_sizing_allowed") is False for p in packets_a),
            "posting_not_allowed": all(p.payload.get("posting_allowed") is False for p in packets_a),
            "dm_not_allowed": all(p.payload.get("dm_allowed") is False for p in packets_a),
            "oos_payload_read_only": all(p.payload.get("read_only") is True for p in packets_a),
            "registry_payload_present": all(bool(p.payload.get("registry_payload")) for p in packets_a),
            "universal_market_present": all(bool(p.payload.get("registry_payload", {}).get("universal_market")) for p in packets_a),
            "social_market_shape": all(
                p.payload.get("registry_payload", {}).get("universal_market", {}).get("market_type") == "social_intelligence"
                for p in packets_a
            ),
            "explanation_present": all(bool(p.payload.get("registry_payload", {}).get("explanation")) for p in packets_a),
            "telemetry_present": all(bool(p.payload.get("registry_payload", {}).get("telemetry")) for p in packets_a),
            "source_engine_id_social": all(
                p.payload.get("source_engine_id") == "oracle.discovery.social_intelligence"
                for p in packets_a
            ),
            "audit_read_only": all(p.audit.get("oracle_read_only") is True for p in packets_a),
            "audit_handoff_target_present": all(
                p.audit.get("handoff_target") == "OOS Opportunity Pipeline"
                for p in packets_a
            ),
            "no_execution_fields_present": all(p.audit.get("execution_fields_present") is False for p in packets_a),
            "no_social_action_fields_present": all(p.audit.get("social_action_fields_present") is False for p in packets_a),
            "audit_execution_not_allowed": all(p.audit.get("execution_allowed") is False for p in packets_a),
            "audit_posting_not_allowed": all(p.audit.get("posting_allowed") is False for p in packets_a),
            "audit_dm_not_allowed": all(p.audit.get("dm_allowed") is False for p in packets_a),
            "immutable_packet_payload": self._check_immutable_payload(packets_a),
        }

        passed = sum(1 for ok in checks.values() if ok)
        failed = sum(1 for ok in checks.values() if not ok)

        telemetry = MappingProxyType({
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
            "deterministic_replay": ids_a == ids_b,
            "oos_validation_ready": checks["all_packets_validation_required"],
            "oos_registry_ready": checks["all_packets_registry_required"],
            "oos_ranking_ready": checks["all_packets_ranking_required"],
            "oos_pipeline_ready": checks["all_packets_pipeline_ready"],
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "broker_connectivity_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
        })

        return SocialIntelligenceOOSRuntimeGateReport(
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
            {"post_id": "post_b", "platform": "X", "author": "macro_trader", "topic": "fed", "text": "Rate cut odds are collapsing after CPI reaction.", "posted_at": "2026-01-15T14:05:00Z", "sentiment": "bearish", "engagement_score": 0.88, "velocity_score": 0.82, "credibility_score": 0.80, "markets": "RATES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
            {"id": "post_a", "network": "reddit", "username": "kalshi_watcher", "category": "prediction_market_social", "content": "Inflation markets are moving fast after the CPI headline.", "time": "2026-01-15T13:35:00Z", "sentiment": "bullish", "engagement": 0.91, "velocity": 0.87, "credibility": 0.76, "affected_markets": ["PREDICTION_MARKETS", "RATES"], "entities": ["CPI", "KALSHI"]},
            {"post_id": "post_minor", "platform": "x", "author": "small_account", "topic": "local", "text": "Random local market comment.", "posted_at": "2026-01-15T12:00:00Z", "sentiment": "neutral", "engagement_score": 0.10, "velocity_score": 0.10, "credibility_score": 0.20, "affected_markets": ["LOCAL"]},
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "SocialIntelligenceOOSRuntimeGateReport",
    "SocialIntelligenceDiscoveryOOSRuntimeGate",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_oos_runtime_gate import (
    SocialIntelligenceDiscoveryOOSRuntimeGate,
)


def test_sid_007_social_intelligence_discovery_oos_runtime_gate():
    gate = SocialIntelligenceDiscoveryOOSRuntimeGate(source_name="sid_007_test_source", min_social_score=0.55)

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["broker_connectivity_allowed"] is False
    assert caps["posting_allowed"] is False
    assert caps["dm_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "SID-007"
    assert report.gate_id == "oracle.discovery.gate.social_intelligence_oos_runtime"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True
    assert len(report.packets) == 2

    assert report.checks["deterministic_replay"] is True
    assert report.checks["all_packets_validation_required"] is True
    assert report.checks["all_packets_ranking_required"] is True
    assert report.checks["all_packets_registry_required"] is True
    assert report.checks["execution_not_allowed"] is True
    assert report.checks["posting_not_allowed"] is True
    assert report.checks["dm_not_allowed"] is True
    assert report.checks["social_market_shape"] is True
    assert report.checks["source_engine_id_social"] is True
    assert report.checks["immutable_packet_payload"] is True

    first = report.packets[0]
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["posting_allowed"] is False
    assert first.payload["dm_allowed"] is False
    assert first.payload["read_only"] is True
    assert first.audit["oracle_read_only"] is True
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    d = report.to_dict()
    assert d["schema_version"] == "SID-007"
    assert d["status"] == "passed"
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["oos_validation_ready"] is True
    assert d["telemetry"]["oos_registry_ready"] is True
    assert d["telemetry"]["oos_ranking_ready"] is True
    assert d["telemetry"]["oos_pipeline_ready"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["posting_allowed"] is False
    assert d["telemetry"]["dm_allowed"] is False

    print("[PASS] SID-007 Social Intelligence Discovery OOS Runtime Gate")
    print({
        "schema_version": d["schema_version"],
        "gate_id": d["gate_id"],
        "status": d["status"],
        "passed_checks": d["passed_checks"],
        "failed_checks": d["failed_checks"],
        "packets": len(d["packets"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_007_social_intelligence_discovery_oos_runtime_gate()
'''

INIT_EXPORT = '''
try:
    from .social_intelligence_discovery_oos_runtime_gate import (
        SocialIntelligenceDiscoveryOOSRuntimeGate,
        SocialIntelligenceOOSRuntimeGateReport,
    )
except Exception:
    pass
'''

GATE_FILE.write_text(GATE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "SocialIntelligenceDiscoveryOOSRuntimeGate" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SID-007 INSTALLER")
print(" Social Intelligence Discovery OOS Runtime Gate")
print("========================================")
print(f"[OK] Wrote {GATE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] SID-007 installed")
print()
print("Run:")
print("py test_sid_007_social_intelligence_discovery_oos_runtime_gate.py")