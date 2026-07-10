from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "news_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

GATE_FILE = MODULE_DIR / "news_intelligence_discovery_oos_runtime_gate.py"
TEST_FILE = ROOT / "test_nid_007_news_intelligence_discovery_oos_runtime_gate.py"
INIT_FILE = MODULE_DIR / "__init__.py"

GATE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .news_intelligence_discovery_pipeline_bridge import NewsIntelligenceDiscoveryPipelineBridge

SCHEMA_VERSION = "NID-007"
GATE_ID = "oracle.discovery.gate.news_intelligence_oos_runtime"


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
class NewsIntelligenceOOSRuntimeGateReport:
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


class NewsIntelligenceDiscoveryOOSRuntimeGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    read_only = True

    def __init__(self, source_name: str = "news_intelligence_oos_runtime_gate_source", min_news_score: float = 0.55) -> None:
        self.source_name = str(source_name)
        self.min_news_score = float(min_news_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "read_only": True,
            "validates": [
                "NID source adapter",
                "NID discovery engine",
                "NID registry bridge",
                "NID pipeline bridge",
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
            "position_sizing_allowed": False,
            "broker_connectivity_allowed": False,
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

    def run(self, raw_records: Sequence[Any] | None = None) -> NewsIntelligenceOOSRuntimeGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        bridge = NewsIntelligenceDiscoveryPipelineBridge()
        report_a = bridge.discover_registry_and_bridge(raw, source_name=self.source_name, min_news_score=self.min_news_score)
        report_b = bridge.discover_registry_and_bridge(tuple(reversed(raw)), source_name=self.source_name, min_news_score=self.min_news_score)

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
            "all_packets_have_article_id": all(bool(p.article_id) for p in packets_a),
            "all_packets_have_title": all(bool(p.title) for p in packets_a),
            "all_packets_validation_required": all(p.payload.get("validation_required") is True for p in packets_a),
            "all_packets_ranking_required": all(p.payload.get("ranking_required") is True for p in packets_a),
            "all_packets_registry_required": all(p.payload.get("registry_required") is True for p in packets_a),
            "execution_not_allowed": all(p.payload.get("execution_allowed") is False for p in packets_a),
            "order_not_allowed": all(p.payload.get("order_allowed") is False for p in packets_a),
            "position_sizing_not_allowed": all(p.payload.get("position_sizing_allowed") is False for p in packets_a),
            "oos_payload_read_only": all(p.payload.get("read_only") is True for p in packets_a),
            "registry_payload_present": all(bool(p.payload.get("registry_payload")) for p in packets_a),
            "universal_market_present": all(bool(p.payload.get("registry_payload", {}).get("universal_market")) for p in packets_a),
            "news_intelligence_market_shape": all(
                p.payload.get("registry_payload", {}).get("universal_market", {}).get("market_type") == "news_intelligence"
                for p in packets_a
            ),
            "explanation_present": all(bool(p.payload.get("registry_payload", {}).get("explanation")) for p in packets_a),
            "telemetry_present": all(bool(p.payload.get("registry_payload", {}).get("telemetry")) for p in packets_a),
            "source_engine_id_present": all(bool(p.payload.get("source_engine_id")) for p in packets_a),
            "source_engine_id_news_intelligence": all(
                p.payload.get("source_engine_id") == "oracle.discovery.news_intelligence"
                for p in packets_a
            ),
            "audit_read_only": all(p.audit.get("oracle_read_only") is True for p in packets_a),
            "audit_handoff_target_present": all(
                p.audit.get("handoff_target") == "OOS Opportunity Pipeline"
                for p in packets_a
            ),
            "no_execution_fields_present": all(p.audit.get("execution_fields_present") is False for p in packets_a),
            "audit_execution_not_allowed": all(p.audit.get("execution_allowed") is False for p in packets_a),
            "audit_order_not_allowed": all(p.audit.get("order_allowed") is False for p in packets_a),
            "audit_position_sizing_not_allowed": all(
                p.audit.get("position_sizing_allowed") is False for p in packets_a
            ),
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
        })

        return NewsIntelligenceOOSRuntimeGateReport(
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
            {"article_id": "article_b", "headline": "Fed signals slower cuts after inflation surprise", "publisher": "MarketWire", "link": "https://example.test/fed", "time": "2026-01-15T14:00:00Z", "category": "fed", "sentiment": "hawkish", "importance": "high", "relevance": 0.91, "markets": "RATES, EQUITIES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
            {"id": "article_a", "title": "CPI comes in hotter than expected", "source": "EconomicDesk", "url": "https://example.test/cpi", "published_at": "2026-01-15T13:30:00Z", "topic": "inflation", "sentiment": "negative", "impact": "high", "relevance_score": 0.95, "affected_markets": ["RATES", "PREDICTION_MARKETS"], "entities": ["CPI", "USD"]},
            {"article_id": "article_minor", "title": "Local market commentary", "source": "SmallWire", "published_at": "2026-01-15T12:00:00Z", "topic": "local", "impact": "low", "relevance_score": 0.20, "affected_markets": ["LOCAL"]},
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "NewsIntelligenceOOSRuntimeGateReport",
    "NewsIntelligenceDiscoveryOOSRuntimeGate",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_oos_runtime_gate import (
    NewsIntelligenceDiscoveryOOSRuntimeGate,
)


def test_nid_007_news_intelligence_discovery_oos_runtime_gate():
    gate = NewsIntelligenceDiscoveryOOSRuntimeGate(source_name="nid_007_test_source", min_news_score=0.55)

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["broker_connectivity_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "NID-007"
    assert report.gate_id == "oracle.discovery.gate.news_intelligence_oos_runtime"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True
    assert len(report.packets) == 2

    assert report.checks["gate_is_read_only"] is True
    assert report.checks["deterministic_replay"] is True
    assert report.checks["all_packets_validation_required"] is True
    assert report.checks["all_packets_ranking_required"] is True
    assert report.checks["all_packets_registry_required"] is True
    assert report.checks["execution_not_allowed"] is True
    assert report.checks["order_not_allowed"] is True
    assert report.checks["position_sizing_not_allowed"] is True
    assert report.checks["news_intelligence_market_shape"] is True
    assert report.checks["source_engine_id_news_intelligence"] is True
    assert report.checks["immutable_packet_payload"] is True

    first = report.packets[0]
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["position_sizing_allowed"] is False
    assert first.payload["read_only"] is True
    assert first.audit["oracle_read_only"] is True
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    d = report.to_dict()
    assert d["schema_version"] == "NID-007"
    assert d["status"] == "passed"
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["oos_validation_ready"] is True
    assert d["telemetry"]["oos_registry_ready"] is True
    assert d["telemetry"]["oos_ranking_ready"] is True
    assert d["telemetry"]["oos_pipeline_ready"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["order_allowed"] is False
    assert d["telemetry"]["position_sizing_allowed"] is False

    print("[PASS] NID-007 News Intelligence Discovery OOS Runtime Gate")
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
    test_nid_007_news_intelligence_discovery_oos_runtime_gate()
'''

INIT_EXPORT = '''
try:
    from .news_intelligence_discovery_oos_runtime_gate import (
        NewsIntelligenceDiscoveryOOSRuntimeGate,
        NewsIntelligenceOOSRuntimeGateReport,
    )
except Exception:
    pass
'''

GATE_FILE.write_text(GATE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "NewsIntelligenceDiscoveryOOSRuntimeGate" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" NID-007 INSTALLER")
print(" News Intelligence Discovery OOS Runtime Gate")
print("========================================")
print(f"[OK] Wrote {GATE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] NID-007 installed")
print()
print("Run:")
print("py test_nid_007_news_intelligence_discovery_oos_runtime_gate.py")