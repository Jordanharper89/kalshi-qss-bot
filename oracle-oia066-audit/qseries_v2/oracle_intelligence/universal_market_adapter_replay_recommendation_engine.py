"""
OI-197 — Oracle Universal Market Adapter Replay Recommendation Engine

Read-only recommendation layer for the Replay Framework.

This engine consumes replay records and canonical ReplayResult-compatible
objects from OI-192 through OI-196 and produces explainable recommendation
artifacts. It does not execute trades, route orders, submit orders, manage
positions, mutate market state, or create execution authority.

Oracle is the Brain. Q Series is the Hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional
import json

try:
    from .universal_market_adapter_replay_contracts import ReplayResult
except Exception:  # pragma: no cover - fallback for standalone inspection
    ReplayResult = None  # type: ignore


READ_ONLY_GUARDRAILS = {
    "oracle_read_only": True,
    "executes_trades": False,
    "routes_orders": False,
    "submits_orders": False,
    "manages_positions": False,
    "execution_owner": "Q_SERIES_ONLY",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _safe_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _safe_records(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_safe_dict(item) for item in value]
    data = _safe_dict(value)
    for key in ("records", "results", "items"):
        items = data.get(key)
        if isinstance(items, list):
            return [_safe_dict(item) for item in items]
    return []


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


@dataclass(frozen=True)
class ReplayRecommendation:
    recommendation_id: str
    recommendation_type: str
    priority: str
    confidence: float
    title: str
    summary: str
    evidence_record_ids: List[str]
    evidence_count: int
    supporting_metrics: Dict[str, Any]
    read_only_guardrails: Dict[str, Any]
    explainability: Dict[str, Any]
    telemetry: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UniversalMarketAdapterReplayRecommendationEngine:
    """
    Generates read-only replay recommendations from replay intelligence output.

    Recommendations are advisory intelligence artifacts only. They are not
    orders, order routes, trade instructions, or position-management actions.
    """

    module_id = "OI-197"
    module_name = "Oracle Universal Market Adapter Replay Recommendation Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._reports: List[Any] = []

    def recommend(
        self,
        replay_input: Any,
        *,
        context: Optional[Mapping[str, Any]] = None,
        max_recommendations: int = 5,
    ) -> Any:
        records = _safe_records(replay_input)
        context_dict = _safe_dict(context)
        recommendations = self._build_recommendations(records, context_dict, max_recommendations)

        telemetry = {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "input_count": len(records),
            "recommendation_count": len(recommendations),
            "context_hash": _hash(context_dict),
            "result_hash": _hash([item.to_dict() for item in recommendations]),
        }

        explainability = {
            "purpose": "Convert replay intelligence into read-only operator recommendations.",
            "read_only_reason": "Recommendations are advisory metadata only and cannot execute, route, submit, or manage positions.",
            "execution_boundary": "Q Series remains the only execution engine.",
            "canonical_contract": "Consumes and returns ReplayResult-compatible structures.",
            "recommendation_dimensions": [
                "confidence concentration",
                "adapter reliability",
                "certification quality",
                "operator review priority",
                "risk visibility",
            ],
        }

        result_records = [item.to_dict() for item in recommendations]
        report = self._make_replay_result(
            records=result_records,
            passed=True,
            status="ok",
            telemetry=telemetry,
            explainability=explainability,
            metadata={
                "recommendation_count": len(recommendations),
                "input_count": len(records),
                "max_recommendations": max_recommendations,
            },
        )
        self._reports.append(report)
        return report

    def recommend_from_engines(
        self,
        *,
        search_result: Any = None,
        filter_result: Any = None,
        query_result: Any = None,
        analytics_result: Any = None,
        intelligence_result: Any = None,
        context: Optional[Mapping[str, Any]] = None,
        max_recommendations: int = 5,
    ) -> Any:
        source = intelligence_result or analytics_result or query_result or filter_result or search_result
        return self.recommend(source, context=context, max_recommendations=max_recommendations)

    def latest_report(self) -> Optional[Any]:
        return self._reports[-1] if self._reports else None

    def reports(self) -> List[Any]:
        return list(self._reports)

    def telemetry_snapshot(self) -> Dict[str, Any]:
        latest = self.latest_report()
        latest_dict = _safe_dict(latest)
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "report_count": len(self._reports),
            "latest_status": latest_dict.get("status"),
            "latest_record_count": latest_dict.get("record_count"),
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _build_recommendations(
        self,
        records: List[Dict[str, Any]],
        context: Dict[str, Any],
        max_recommendations: int,
    ) -> List[ReplayRecommendation]:
        recommendations: List[ReplayRecommendation] = []
        if not records:
            recommendations.append(self._recommendation(
                recommendation_type="operator_review",
                priority="low",
                confidence=0.0,
                title="No replay records available for recommendation.",
                summary="Oracle could not generate replay recommendations because no replay records were supplied.",
                evidence=[],
                metrics={"input_count": 0},
                reasons=["No records were supplied to the recommendation engine."],
            ))
            return recommendations[:max_recommendations]

        certified = [record for record in records if bool(record.get("certified", record.get("passed", False)))]
        high_confidence = [record for record in records if _float(record.get("confidence"), 0.0) >= 0.80]
        warnings = [record for record in records if str(record.get("certification_level", "")).lower() == "certified_with_warnings"]
        rejected = [record for record in records if str(record.get("certification_level", "")).lower() == "not_certified" or bool(record.get("certified")) is False]

        adapter_counts: Dict[str, int] = {}
        for record in records:
            adapter = str(record.get("adapter_id") or record.get("adapter") or "unknown.adapter")
            adapter_counts[adapter] = adapter_counts.get(adapter, 0) + 1
        dominant_adapter = max(adapter_counts.items(), key=lambda item: item[1])[0] if adapter_counts else "unknown.adapter"

        if high_confidence:
            recommendations.append(self._recommendation(
                recommendation_type="high_confidence_replay_review",
                priority="high",
                confidence=min(1.0, sum(_float(r.get("confidence"), 0.0) for r in high_confidence) / len(high_confidence)),
                title="Prioritize high-confidence replay artifacts for operator review.",
                summary="Replay evidence contains high-confidence artifacts that deserve review before future decision packaging.",
                evidence=high_confidence,
                metrics={"high_confidence_count": len(high_confidence), "threshold": 0.80},
                reasons=["High-confidence replay records indicate historically stronger intelligence quality."],
            ))

        if certified:
            recommendations.append(self._recommendation(
                recommendation_type="certified_replay_baseline",
                priority="medium",
                confidence=min(1.0, len(certified) / max(1, len(records))),
                title="Use certified replay artifacts as the baseline intelligence set.",
                summary="Certified replay artifacts should be treated as the trusted baseline for downstream Oracle analysis.",
                evidence=certified,
                metrics={"certified_count": len(certified), "input_count": len(records)},
                reasons=["Certified records passed replay validation and certification checks."],
            ))

        if warnings:
            recommendations.append(self._recommendation(
                recommendation_type="warning_review",
                priority="medium",
                confidence=0.65,
                title="Review replay artifacts certified with warnings.",
                summary="Some certified artifacts include warnings and should be reviewed before being promoted into stronger intelligence packages.",
                evidence=warnings,
                metrics={"warning_count": len(warnings)},
                reasons=["Warnings are non-blocking but should remain visible to operators."],
            ))

        if rejected:
            recommendations.append(self._recommendation(
                recommendation_type="risk_visibility",
                priority="medium",
                confidence=0.55,
                title="Preserve rejected replay artifacts for risk learning.",
                summary="Rejected artifacts should remain searchable because failed replay outcomes can improve future Oracle quality controls.",
                evidence=rejected,
                metrics={"rejected_count": len(rejected)},
                reasons=["Rejected records can reveal weak adapters, stale signals, or failed replay assumptions."],
            ))

        if dominant_adapter != "unknown.adapter":
            recommendations.append(self._recommendation(
                recommendation_type="adapter_pattern_review",
                priority="low",
                confidence=min(1.0, adapter_counts[dominant_adapter] / max(1, len(records))),
                title=f"Review adapter concentration for {dominant_adapter}.",
                summary="Replay evidence is concentrated around one adapter. This can be useful, but it should be monitored for over-reliance.",
                evidence=[record for record in records if str(record.get("adapter_id") or record.get("adapter")) == dominant_adapter],
                metrics={"adapter_id": dominant_adapter, "adapter_count": adapter_counts[dominant_adapter]},
                reasons=["Adapter concentration can reveal useful patterns or hidden dependency risk."],
            ))

        return recommendations[:max_recommendations]

    def _recommendation(
        self,
        *,
        recommendation_type: str,
        priority: str,
        confidence: float,
        title: str,
        summary: str,
        evidence: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        reasons: List[str],
    ) -> ReplayRecommendation:
        evidence_ids = [
            str(record.get("registration_id") or record.get("manifest_id") or record.get("certification_id") or _hash(record)[:16])
            for record in evidence
        ]
        payload = {
            "oracle_instance_id": self.oracle_instance_id,
            "recommendation_type": recommendation_type,
            "priority": priority,
            "confidence": round(float(confidence), 6),
            "evidence_ids": evidence_ids,
            "metrics": metrics,
            "title": title,
        }
        rec_hash = _hash(payload)
        return ReplayRecommendation(
            recommendation_id="oi197.recommendation." + rec_hash[:24],
            recommendation_type=recommendation_type,
            priority=priority,
            confidence=round(float(confidence), 6),
            title=title,
            summary=summary,
            evidence_record_ids=evidence_ids,
            evidence_count=len(evidence),
            supporting_metrics=dict(metrics),
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            explainability={
                "reasoning": list(reasons),
                "read_only_reason": "The recommendation is advisory only and creates no execution authority.",
                "execution_boundary": "Q Series remains the only execution engine.",
            },
            telemetry={
                "module_id": self.module_id,
                "oracle_instance_id": self.oracle_instance_id,
                "recommendation_type": recommendation_type,
                "priority": priority,
                "confidence": round(float(confidence), 6),
                "evidence_count": len(evidence),
                "recommendation_hash": rec_hash,
            },
        )

    def _make_replay_result(
        self,
        *,
        records: List[Dict[str, Any]],
        passed: bool,
        status: str,
        telemetry: Dict[str, Any],
        explainability: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Any:
        if ReplayResult is not None:
            try:
                return ReplayResult(
                    module_id=self.module_id,
                    module_name=self.module_name,
                    oracle_instance_id=self.oracle_instance_id,
                    passed=passed,
                    status=status,
                    record_count=len(records),
                    records=records,
                    telemetry=telemetry,
                    explainability=explainability,
                    metadata=metadata,
                    read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
                )
            except TypeError:
                pass
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "passed": passed,
            "status": status,
            "record_count": len(records),
            "records": records,
            "telemetry": telemetry,
            "explainability": explainability,
            "metadata": metadata,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }


def create_replay_recommendation_engine(
    oracle_instance_id: str = "oracle.default",
) -> UniversalMarketAdapterReplayRecommendationEngine:
    return UniversalMarketAdapterReplayRecommendationEngine(oracle_instance_id=oracle_instance_id)


def create_universal_market_adapter_replay_recommendation_engine(
    oracle_instance_id: str = "oracle.default",
) -> UniversalMarketAdapterReplayRecommendationEngine:
    return create_replay_recommendation_engine(oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplayRecommendation",
    "UniversalMarketAdapterReplayRecommendationEngine",
    "create_replay_recommendation_engine",
    "create_universal_market_adapter_replay_recommendation_engine",
]
