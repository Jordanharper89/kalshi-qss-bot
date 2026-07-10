
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .social_intelligence_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    SocialIntelligenceDiscoveryRequest,
    SocialIntelligenceFamily,
)
from .social_intelligence_source_adapter import SocialIntelligenceSourceAdapter
from .social_intelligence_discovery_engine import SocialIntelligenceDiscoveryEngine
from .social_intelligence_discovery_pipeline_gate import SocialIntelligenceDiscoveryPipelineGate
from .social_intelligence_discovery_registry_bridge import SocialIntelligenceDiscoveryRegistryBridge
from .social_intelligence_discovery_pipeline_bridge import SocialIntelligenceDiscoveryPipelineBridge
from .social_intelligence_discovery_oos_runtime_gate import SocialIntelligenceDiscoveryOOSRuntimeGate
from .social_intelligence_discovery_replay_ledger import SocialIntelligenceDiscoveryReplayLedger

SCHEMA_VERSION = "SID-009"
GATE_ID = "oracle.discovery.gate.social_intelligence_subsystem_integration"


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
class SocialIntelligenceSubsystemIntegrationReport:
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


class SocialIntelligenceSubsystemIntegrationGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    read_only = True

    def __init__(self, source_name: str = "social_intelligence_subsystem_gate_source", min_social_score: float = 0.55) -> None:
        self.source_name = str(source_name)
        self.min_social_score = float(min_social_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "read_only": True,
            "validates": [
                "SID-001 contract",
                "SID-002 source adapter",
                "SID-003 discovery engine",
                "SID-004 pipeline gate",
                "SID-005 registry bridge",
                "SID-006 pipeline bridge",
                "SID-007 OOS runtime gate",
                "SID-008 replay ledger",
            ],
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "broker_connectivity_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
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

    def run(self, raw_records: Sequence[Any] | None = None) -> SocialIntelligenceSubsystemIntegrationReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = SocialIntelligenceSourceAdapter(source_name=self.source_name)
        batch = adapter.normalize_batch(raw)

        request = SocialIntelligenceDiscoveryRequest(
            request_id="sid009.social.intelligence.subsystem.integration",
            family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
            source_name=self.source_name,
            post_ids=tuple(sorted({s.post_id for s in batch.snapshots})),
            topics=tuple(sorted({s.topic for s in batch.snapshots})),
            markets=tuple(sorted({m for s in batch.snapshots for m in s.affected_markets})),
            metadata={"snapshots": batch.snapshots},
        )

        engine = SocialIntelligenceDiscoveryEngine(min_social_score=self.min_social_score)
        discovery_report = engine.discover(request)

        pipeline_gate = SocialIntelligenceDiscoveryPipelineGate(
            source_name=self.source_name,
            min_social_score=self.min_social_score,
        )
        pipeline_gate_report = pipeline_gate.run(raw)

        registry_bridge = SocialIntelligenceDiscoveryRegistryBridge()
        registry_report = registry_bridge.bridge_report(discovery_report)

        pipeline_bridge = SocialIntelligenceDiscoveryPipelineBridge()
        pipeline_report = pipeline_bridge.bridge_records(registry_report.records)

        oos_gate = SocialIntelligenceDiscoveryOOSRuntimeGate(
            source_name=self.source_name,
            min_social_score=self.min_social_score,
        )
        oos_report = oos_gate.run(raw)

        replay_ledger = SocialIntelligenceDiscoveryReplayLedger()
        replay_a = replay_ledger.record_packets(oos_report.packets)
        replay_b = replay_ledger.record_packets(oos_gate.run(tuple(reversed(raw))).packets)
        replay_compare = replay_ledger.compare(replay_a, replay_b)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "contract_schema_ok": CONTRACT_SCHEMA_VERSION == "SID-001",
            "request_is_read_only": request.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "pipeline_gate_is_read_only": pipeline_gate.read_only is True,
            "registry_bridge_is_read_only": registry_bridge.read_only is True,
            "pipeline_bridge_is_read_only": pipeline_bridge.read_only is True,
            "oos_gate_is_read_only": oos_gate.read_only is True,
            "replay_ledger_is_read_only": replay_ledger.read_only is True,

            "adapter_schema_ok": batch.schema_version == "SID-002",
            "engine_contract_schema_ok": discovery_report.schema_version == "SID-001",
            "engine_runtime_schema_ok": engine.schema_version == "SID-003",
            "pipeline_gate_schema_ok": pipeline_gate_report.schema_version == "SID-004",
            "registry_bridge_schema_ok": registry_report.schema_version == "SID-005",
            "pipeline_bridge_schema_ok": pipeline_report.schema_version == "SID-006",
            "oos_gate_schema_ok": oos_report.schema_version == "SID-007",
            "replay_ledger_schema_ok": replay_a.schema_version == "SID-008",

            "snapshots_emitted": len(batch.snapshots) == len(raw),
            "posts_seen": discovery_report.telemetry.posts_seen == 3,
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

            "all_social_markets_shape": all(
                o.universal_market.get("market_type") == "social_intelligence"
                and o.universal_market.get("execution_allowed") is False
                and o.universal_market.get("order_allowed") is False
                and o.universal_market.get("position_sizing_allowed") is False
                and o.universal_market.get("posting_allowed") is False
                and o.universal_market.get("dm_allowed") is False
                for o in discovery_report.opportunities
            ),
            "all_pipeline_packets_validation_ready": all(p.payload.get("validation_required") is True for p in pipeline_report.packets),
            "all_pipeline_packets_registry_ready": all(p.payload.get("registry_required") is True for p in pipeline_report.packets),
            "all_pipeline_packets_ranking_ready": all(p.payload.get("ranking_required") is True for p in pipeline_report.packets),
            "execution_not_allowed": all(p.payload.get("execution_allowed") is False for p in pipeline_report.packets),
            "order_not_allowed": all(p.payload.get("order_allowed") is False for p in pipeline_report.packets),
            "position_sizing_not_allowed": all(p.payload.get("position_sizing_allowed") is False for p in pipeline_report.packets),
            "posting_not_allowed": all(p.payload.get("posting_allowed") is False for p in pipeline_report.packets),
            "dm_not_allowed": all(p.payload.get("dm_allowed") is False for p in pipeline_report.packets),
            "no_execution_fields_in_registry": all(r.audit.get("execution_fields_present") is False for r in registry_report.records),
            "no_social_action_fields_in_registry": all(r.audit.get("social_action_fields_present") is False for r in registry_report.records),
            "no_execution_fields_in_pipeline": all(p.audit.get("execution_fields_present") is False for p in pipeline_report.packets),
            "no_social_action_fields_in_pipeline": all(p.audit.get("social_action_fields_present") is False for p in pipeline_report.packets),

            "immutable_registry_payload": self._immutable_mapping_check(registry_report.records[0].payload if registry_report.records else {}),
            "immutable_pipeline_payload": self._immutable_mapping_check(pipeline_report.packets[0].payload if pipeline_report.packets else {}),
            "immutable_replay_summary": self._immutable_mapping_check(replay_a.entries[0].payload_summary if replay_a.entries else {}),

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

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "raw_records_seen": len(raw),
            "snapshots_emitted": len(batch.snapshots),
            "posts_seen": discovery_report.telemetry.posts_seen,
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
            "position_sizing_allowed": False,
            "broker_connectivity_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
            "replay_match": replay_compare.matching,
            "run_fingerprint": replay_a.run_fingerprint,
        })

        return SocialIntelligenceSubsystemIntegrationReport(
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
            {"post_id": "post_b", "platform": "X", "author": "macro_trader", "topic": "fed", "text": "Rate cut odds are collapsing after CPI reaction.", "posted_at": "2026-01-15T14:05:00Z", "sentiment": "bearish", "engagement_score": 0.88, "velocity_score": 0.82, "credibility_score": 0.80, "markets": "RATES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
            {"id": "post_a", "network": "reddit", "username": "kalshi_watcher", "category": "prediction_market_social", "content": "Inflation markets are moving fast after the CPI headline.", "time": "2026-01-15T13:35:00Z", "sentiment": "bullish", "engagement": 0.91, "velocity": 0.87, "credibility": 0.76, "affected_markets": ["PREDICTION_MARKETS", "RATES"], "entities": ["CPI", "KALSHI"]},
            {"post_id": "post_minor", "platform": "x", "author": "small_account", "topic": "local", "text": "Random local market comment.", "posted_at": "2026-01-15T12:00:00Z", "sentiment": "neutral", "engagement_score": 0.10, "velocity_score": 0.10, "credibility_score": 0.20, "affected_markets": ["LOCAL"]},
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "SocialIntelligenceSubsystemIntegrationReport",
    "SocialIntelligenceSubsystemIntegrationGate",
]
