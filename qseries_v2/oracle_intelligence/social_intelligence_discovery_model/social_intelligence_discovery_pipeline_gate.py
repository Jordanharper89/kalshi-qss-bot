
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .social_intelligence_discovery_contract import SocialIntelligenceDiscoveryRequest, SocialIntelligenceFamily
from .social_intelligence_source_adapter import SocialIntelligenceSourceAdapter
from .social_intelligence_discovery_engine import SocialIntelligenceDiscoveryEngine

SCHEMA_VERSION = "SID-004"
GATE_ID = "oracle.discovery.gate.social_intelligence_pipeline"


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
class SocialIntelligenceDiscoveryGateReport:
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


class SocialIntelligenceDiscoveryPipelineGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    read_only = True

    def __init__(self, source_name: str = "social_intelligence_gate_source", min_social_score: float = 0.55) -> None:
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

    def run(self, raw_records: Sequence[Any] | None = None) -> SocialIntelligenceDiscoveryGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = SocialIntelligenceSourceAdapter(source_name=self.source_name)
        batch_a = adapter.normalize_batch(raw)
        batch_b = adapter.normalize_batch(tuple(reversed(raw)))

        request_a = SocialIntelligenceDiscoveryRequest(
            request_id="sid004.pipeline.gate.a",
            family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
            source_name=self.source_name,
            post_ids=tuple(sorted({s.post_id for s in batch_a.snapshots})),
            topics=tuple(sorted({s.topic for s in batch_a.snapshots})),
            markets=tuple(sorted({m for s in batch_a.snapshots for m in s.affected_markets})),
            metadata={"snapshots": batch_a.snapshots},
        )
        request_b = SocialIntelligenceDiscoveryRequest(
            request_id="sid004.pipeline.gate.b",
            family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
            source_name=self.source_name,
            post_ids=tuple(sorted({s.post_id for s in batch_b.snapshots})),
            topics=tuple(sorted({s.topic for s in batch_b.snapshots})),
            markets=tuple(sorted({m for s in batch_b.snapshots for m in s.affected_markets})),
            metadata={"snapshots": batch_b.snapshots},
        )

        engine = SocialIntelligenceDiscoveryEngine(min_social_score=self.min_social_score)
        report_a = engine.discover(request_a)
        report_b = engine.discover(request_b)

        ids_a = tuple(o.opportunity_id for o in report_a.opportunities)
        ids_b = tuple(o.opportunity_id for o in report_b.opportunities)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "batch_is_read_only": batch_a.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "discovery_report_is_read_only": report_a.read_only is True,
            "adapter_schema_ok": batch_a.schema_version == "SID-002",
            "engine_contract_schema_ok": report_a.schema_version == "SID-001",
            "engine_runtime_schema_ok": engine.schema_version == "SID-003",
            "raw_records_seen": batch_a.telemetry.get("raw_records_seen") == len(raw),
            "snapshots_emitted": len(batch_a.snapshots) == len(raw),
            "posts_seen": batch_a.telemetry.get("posts_seen") == 3,
            "adapter_deterministic_order": tuple(s.post_id for s in batch_a.snapshots) == tuple(s.post_id for s in batch_b.snapshots),
            "engine_emits_opportunities": len(report_a.opportunities) == 2,
            "engine_replay_deterministic": ids_a == ids_b,
            "all_opportunities_read_only": all(o.read_only is True for o in report_a.opportunities),
            "all_opportunities_have_ids": all(bool(o.opportunity_id) for o in report_a.opportunities),
            "all_opportunities_have_post_id": all(bool(o.post_id) for o in report_a.opportunities),
            "all_opportunities_have_topic": all(bool(o.topic) for o in report_a.opportunities),
            "all_opportunities_have_score": all(o.social_score >= self.min_social_score for o in report_a.opportunities),
            "all_opportunities_have_confidence": all(0.0 <= o.confidence <= 1.0 for o in report_a.opportunities),
            "all_opportunities_have_explanation": all(bool(o.explanation) for o in report_a.opportunities),
            "all_opportunities_have_telemetry": all(bool(o.telemetry) for o in report_a.opportunities),
            "universal_market_shape": all(
                o.universal_market.get("market_type") == "social_intelligence"
                and o.universal_market.get("read_only") is True
                and o.universal_market.get("execution_allowed") is False
                and o.universal_market.get("order_allowed") is False
                and o.universal_market.get("position_sizing_allowed") is False
                and o.universal_market.get("posting_allowed") is False
                and o.universal_market.get("dm_allowed") is False
                for o in report_a.opportunities
            ),
            "source_engine_id_present": all(
                o.source_engine_id == "oracle.discovery.social_intelligence"
                for o in report_a.opportunities
            ),
            "telemetry_present": bool(batch_a.telemetry) and bool(report_a.telemetry),
            "no_execution_or_social_action_fields": all(
                not hasattr(o, "order_id")
                and not hasattr(o, "position_size")
                and not hasattr(o, "execution_id")
                and not hasattr(o, "route_id")
                and not hasattr(o, "post_action_id")
                and not hasattr(o, "dm_action_id")
                for o in report_a.opportunities
            ),
            "immutable_universal_market": self._check_immutable_market(report_a),
        }

        passed = sum(1 for ok in checks.values() if ok)
        failed = sum(1 for ok in checks.values() if not ok)

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "raw_records_seen": len(raw),
            "snapshots_emitted": len(batch_a.snapshots),
            "posts_seen": batch_a.telemetry.get("posts_seen"),
            "opportunities_emitted": len(report_a.opportunities),
            "passed_checks": passed,
            "failed_checks": failed,
            "warning_count": 0,
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
            "deterministic_replay": ids_a == ids_b,
        })

        return SocialIntelligenceDiscoveryGateReport(
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

    def _check_immutable_market(self, report: Any) -> bool:
        if not report.opportunities:
            return False
        try:
            report.opportunities[0].universal_market["execution_allowed"] = True
            return False
        except TypeError:
            return True

    def _fixture_records(self) -> Tuple[Mapping[str, Any], ...]:
        return (
            {
                "post_id": "post_b",
                "platform": "X",
                "author": "macro_trader",
                "topic": "fed",
                "text": "Rate cut odds are collapsing after CPI reaction.",
                "posted_at": "2026-01-15T14:05:00Z",
                "sentiment": "bearish",
                "engagement_score": 0.88,
                "velocity_score": 0.82,
                "credibility_score": 0.80,
                "markets": "RATES, PREDICTION_MARKETS",
                "symbols": "FED, CPI",
            },
            {
                "id": "post_a",
                "network": "reddit",
                "username": "kalshi_watcher",
                "category": "prediction_market_social",
                "content": "Inflation markets are moving fast after the CPI headline.",
                "time": "2026-01-15T13:35:00Z",
                "sentiment": "bullish",
                "engagement": 0.91,
                "velocity": 0.87,
                "credibility": 0.76,
                "affected_markets": ["PREDICTION_MARKETS", "RATES"],
                "entities": ["CPI", "KALSHI"],
            },
            {
                "post_id": "post_minor",
                "platform": "x",
                "author": "small_account",
                "topic": "local",
                "text": "Random local market comment.",
                "posted_at": "2026-01-15T12:00:00Z",
                "sentiment": "neutral",
                "engagement_score": 0.10,
                "velocity_score": 0.10,
                "credibility_score": 0.20,
                "affected_markets": ["LOCAL"],
            },
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "SocialIntelligenceDiscoveryGateReport",
    "SocialIntelligenceDiscoveryPipelineGate",
]
