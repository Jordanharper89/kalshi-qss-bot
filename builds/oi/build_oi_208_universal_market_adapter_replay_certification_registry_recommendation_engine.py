from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_certification_registry_recommendation_engine.py"
TEST = ROOT / "test_oi_208_universal_market_adapter_replay_certification_registry_recommendation_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

ENGINE_ID = "OI-208"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Certification Registry Recommendation Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ReplayCertificationRegistryRecommendation:
    recommendation_id: str
    recommendation_type: str
    priority: str
    confidence: float
    title: str
    detail: str
    action: str
    reason_codes: Tuple[str, ...] = field(default_factory=tuple)
    supporting_signals: Tuple[str, ...] = field(default_factory=tuple)
    telemetry: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        data["supporting_signals"] = list(self.supporting_signals)
        return data


@dataclass(frozen=True)
class ReplayCertificationRegistryRecommendationResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    recommendation_count: int
    intelligence_score: float
    recommendations: Tuple[ReplayCertificationRegistryRecommendation, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "recommendation_count": self.recommendation_count,
            "intelligence_score": self.intelligence_score,
            "recommendations": [rec.to_dict() for rec in self.recommendations],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayCertificationRegistryRecommendationEngine:
    """
    Converts OI-207 registry intelligence into read-only Oracle recommendations.

    This engine recommends Oracle review actions only.
    It never executes, routes orders, or manages positions.
    """

    def recommend(
        self,
        intelligence: Any,
        *,
        limit: Optional[int] = None,
    ) -> ReplayCertificationRegistryRecommendationResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        intelligence_map = self._to_mapping(intelligence)
        signals = self._extract_signals(intelligence_map)
        intelligence_score = self._clamp01(self._number(intelligence_map, "intelligence_score", default=0.0))

        recommendations: List[ReplayCertificationRegistryRecommendation] = []

        if not signals:
            recommendations.append(
                self._build_recommendation(
                    recommendation_type="hold",
                    priority="medium",
                    confidence=0.50,
                    title="Hold registry cohort for additional Oracle evidence.",
                    detail="No registry intelligence signals were available.",
                    action="Hold this registry cohort until OI-207 produces explainable intelligence signals.",
                    reason_codes=("NO_REGISTRY_INTELLIGENCE_SIGNALS", "READ_ONLY_ORACLE_RECOMMENDATION"),
                    supporting_signals=tuple(),
                )
            )

        for signal in signals:
            signal_id = str(signal.get("signal_id", "UNKNOWN_SIGNAL"))
            category = str(signal.get("category", "context")).lower()
            severity = str(signal.get("severity", "info")).lower()
            score = self._clamp01(self._number(signal, "score", default=0.0))
            title = str(signal.get("title", signal_id))
            explanation = str(signal.get("explanation", ""))
            upstream_recommendation = str(signal.get("recommendation", ""))

            if category == "strength" or severity == "positive":
                recommendations.append(
                    self._build_recommendation(
                        recommendation_type="promote",
                        priority=self._priority(intelligence_score, score, positive=True),
                        confidence=max(intelligence_score, score),
                        title=f"Promote registry intelligence: {title}",
                        detail=explanation,
                        action=(
                            "Promote this replay certification registry cohort to downstream read-only "
                            "Oracle review. Do not execute; Q Series remains execution owner."
                        ),
                        reason_codes=(
                            "REGISTRY_STRENGTH_SIGNAL",
                            "PROMOTE_TO_ORACLE_REVIEW",
                            "READ_ONLY_ORACLE_RECOMMENDATION",
                            "Q_SERIES_EXECUTION_REQUIRED",
                        ),
                        supporting_signals=(signal_id,),
                    )
                )
            elif category == "risk" or severity == "warning":
                recommendations.append(
                    self._build_recommendation(
                        recommendation_type="review",
                        priority="high",
                        confidence=max(0.50, 1.0 - score),
                        title=f"Review registry risk: {title}",
                        detail=explanation,
                        action=(
                            "Hold this replay certification registry cohort for additional Oracle inspection "
                            "before downstream promotion."
                        ),
                        reason_codes=(
                            "REGISTRY_RISK_SIGNAL",
                            "REQUIRES_ORACLE_REVIEW",
                            "READ_ONLY_ORACLE_RECOMMENDATION",
                            "Q_SERIES_EXECUTION_REQUIRED",
                        ),
                        supporting_signals=(signal_id,),
                    )
                )
            else:
                recommendations.append(
                    self._build_recommendation(
                        recommendation_type="monitor",
                        priority="medium" if intelligence_score >= 0.60 else "low",
                        confidence=max(0.40, min(0.75, intelligence_score)),
                        title=f"Monitor registry context: {title}",
                        detail=explanation or upstream_recommendation,
                        action=(
                            "Continue read-only Oracle monitoring and preserve registry telemetry for replay."
                        ),
                        reason_codes=(
                            "REGISTRY_CONTEXT_SIGNAL",
                            "CONTINUE_MONITORING",
                            "READ_ONLY_ORACLE_RECOMMENDATION",
                        ),
                        supporting_signals=(signal_id,),
                    )
                )

        recommendations = self._dedupe(recommendations)
        recommendations = sorted(
            recommendations,
            key=lambda rec: (self._priority_rank(rec.priority), rec.confidence, rec.recommendation_id),
            reverse=True,
        )

        if limit is not None:
            recommendations = recommendations[: max(0, int(limit))]

        status = self._status(recommendations)

        return ReplayCertificationRegistryRecommendationResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            recommendation_count=len(recommendations),
            intelligence_score=intelligence_score,
            recommendations=tuple(recommendations),
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "read_only": True,
                "oracle_role": "brain",
                "execution_owner": "Q Series",
                "does_not_execute": True,
                "does_not_route_orders": True,
                "does_not_manage_positions": True,
                "input_engine_id": intelligence_map.get("engine_id"),
                "canonical_input": "ReplayCertificationRegistryIntelligenceResult compatible",
                "canonical_output": "ReplayCertificationRegistryRecommendationResult",
                "signals_count": len(signals),
                "recommendation_count": len(recommendations),
                "recommendations_are_advisory": True,
                "explainability": True,
                "replayability": True,
            },
            explanation=(
                f"Generated {len(recommendations)} read-only registry recommendation(s) from "
                f"{len(signals)} intelligence signal(s). Oracle recommendations are advisory only; "
                "Q Series remains the only execution engine."
            ),
        )

    def _build_recommendation(
        self,
        *,
        recommendation_type: str,
        priority: str,
        confidence: float,
        title: str,
        detail: str,
        action: str,
        reason_codes: Tuple[str, ...],
        supporting_signals: Tuple[str, ...],
    ) -> ReplayCertificationRegistryRecommendation:
        stable = {
            "type": recommendation_type,
            "priority": priority,
            "title": title,
            "reason_codes": reason_codes,
            "supporting_signals": supporting_signals,
        }
        digest = sha256(repr(stable).encode("utf-8")).hexdigest()[:14]
        return ReplayCertificationRegistryRecommendation(
            recommendation_id=f"replay_registry_rec_{digest}",
            recommendation_type=recommendation_type,
            priority=priority,
            confidence=round(self._clamp01(confidence), 6),
            title=title,
            detail=detail,
            action=action,
            reason_codes=reason_codes,
            supporting_signals=supporting_signals,
            telemetry={
                "engine_id": ENGINE_ID,
                "read_only": True,
                "oracle_role": "brain",
                "execution_owner": "Q Series",
                "does_not_execute": True,
                "recommendation_is_advisory": True,
            },
        )

    def _extract_signals(self, intelligence_map: Mapping[str, Any]) -> List[Dict[str, Any]]:
        raw = intelligence_map.get("signals", [])
        if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
            return []
        output: List[Dict[str, Any]] = []
        for item in raw:
            mapped = self._to_mapping(item)
            if mapped:
                output.append(mapped)
        return output

    def _dedupe(
        self,
        recommendations: List[ReplayCertificationRegistryRecommendation],
    ) -> List[ReplayCertificationRegistryRecommendation]:
        seen: set[str] = set()
        output: List[ReplayCertificationRegistryRecommendation] = []
        for rec in recommendations:
            if rec.recommendation_id in seen:
                continue
            seen.add(rec.recommendation_id)
            output.append(rec)
        return output

    def _priority(self, intelligence_score: float, signal_score: float, *, positive: bool) -> str:
        combined = (float(intelligence_score) + float(signal_score)) / 2.0
        if positive and combined >= 0.75:
            return "high"
        if combined >= 0.55:
            return "medium"
        return "low"

    def _priority_rank(self, priority: str) -> int:
        return {"high": 3, "medium": 2, "low": 1}.get(priority, 0)

    def _status(self, recommendations: List[ReplayCertificationRegistryRecommendation]) -> str:
        if not recommendations:
            return "empty"
        if any(rec.recommendation_type == "review" for rec in recommendations):
            return "review"
        if any(rec.recommendation_type == "promote" for rec in recommendations):
            return "ok"
        return "monitor"

    def _to_mapping(self, item: Any) -> Dict[str, Any]:
        if item is None:
            return {}
        if isinstance(item, Mapping):
            return dict(item)
        if hasattr(item, "to_dict") and callable(item.to_dict):
            mapped = item.to_dict()
            if isinstance(mapped, Mapping):
                return dict(mapped)
        if hasattr(item, "__dict__"):
            return dict(vars(item))
        return {}

    def _number(self, data: Mapping[str, Any], key: str, *, default: float = 0.0) -> float:
        try:
            return float(data.get(key, default))
        except (TypeError, ValueError):
            return float(default)

    def _clamp01(self, value: float) -> float:
        value = float(value)
        if value > 1.0 and value <= 100.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))


def recommend_replay_certification_registry_actions(
    intelligence: Any,
    *,
    limit: Optional[int] = None,
) -> ReplayCertificationRegistryRecommendationResult:
    return UniversalMarketAdapterReplayCertificationRegistryRecommendationEngine().recommend(
        intelligence,
        limit=limit,
    )


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayCertificationRegistryRecommendation",
    "ReplayCertificationRegistryRecommendationResult",
    "UniversalMarketAdapterReplayCertificationRegistryRecommendationEngine",
    "recommend_replay_certification_registry_actions",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_recommendation_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryRecommendationEngine,
    recommend_replay_certification_registry_actions,
)


def test_strength_signal_creates_promote_recommendation():
    intelligence = {
        "engine_id": "OI-207",
        "status": "good",
        "intelligence_score": 0.72,
        "signals": [
            {
                "signal_id": "SIG_STRENGTH",
                "category": "strength",
                "severity": "positive",
                "score": 0.90,
                "title": "Certified cohort strength.",
                "explanation": "Registry cohort is constructive.",
                "recommendation": "Forward to review.",
            }
        ],
    }

    result = UniversalMarketAdapterReplayCertificationRegistryRecommendationEngine().recommend(intelligence)

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.recommendation_count == 1
    assert result.recommendations[0].recommendation_type == "promote"
    assert result.recommendations[0].priority == "high"
    assert "Q_SERIES_EXECUTION_REQUIRED" in result.recommendations[0].reason_codes
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert result.telemetry["input_engine_id"] == "OI-207"


def test_warning_signal_creates_review_recommendation():
    result = recommend_replay_certification_registry_actions(
        {
            "engine_id": "OI-207",
            "status": "review",
            "intelligence_score": 0.38,
            "signals": [
                {
                    "signal_id": "SIG_RISK",
                    "category": "risk",
                    "severity": "warning",
                    "score": 0.30,
                    "title": "Weak registry cohort.",
                    "explanation": "Registry cohort requires review.",
                    "recommendation": "Hold.",
                }
            ],
        }
    )

    assert result.status == "review"
    assert result.recommendation_count == 1
    assert result.recommendations[0].recommendation_type == "review"
    assert result.recommendations[0].priority == "high"
    assert "REGISTRY_RISK_SIGNAL" in result.recommendations[0].reason_codes


def test_empty_signals_create_hold_recommendation():
    result = recommend_replay_certification_registry_actions(
        {"engine_id": "OI-207", "status": "review", "intelligence_score": 0.50, "signals": []}
    )

    assert result.status == "monitor"
    assert result.recommendation_count == 1
    assert result.recommendations[0].recommendation_type == "hold"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


def test_limit_is_respected():
    result = recommend_replay_certification_registry_actions(
        {
            "engine_id": "OI-207",
            "intelligence_score": 0.70,
            "signals": [
                {"signal_id": "S1", "category": "strength", "severity": "positive", "score": 0.90, "title": "A"},
                {"signal_id": "S2", "category": "context", "severity": "info", "score": 0.60, "title": "B"},
            ],
        },
        limit=1,
    )

    assert result.recommendation_count == 1


if __name__ == "__main__":
    test_strength_signal_creates_promote_recommendation()
    test_warning_signal_creates_review_recommendation()
    test_empty_signals_create_hold_recommendation()
    test_limit_is_respected()

    print("[PASS] OI-208 Universal Market Adapter Replay Certification Registry Recommendation Engine")
    print(
        recommend_replay_certification_registry_actions(
            {
                "engine_id": "OI-207",
                "status": "good",
                "intelligence_score": 0.72,
                "signals": [
                    {
                        "signal_id": "SIG_DEMO",
                        "category": "strength",
                        "severity": "positive",
                        "score": 0.90,
                        "title": "Demo registry strength.",
                        "explanation": "Replay certification registry intelligence is constructive.",
                        "recommendation": "Forward to read-only Oracle review.",
                    }
                ],
            }
        ).to_dict()
    )
'''


def ensure_package() -> None:
    PKG.mkdir(parents=True, exist_ok=True)
    if not INIT.exists():
        INIT.write_text("", encoding="utf-8")


def update_init() -> None:
    export_line = (
        "from .universal_market_adapter_replay_certification_registry_recommendation_engine import "
        "UniversalMarketAdapterReplayCertificationRegistryRecommendationEngine, "
        "recommend_replay_certification_registry_actions\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-208 INSTALLER")
    print(" Universal Market Adapter Replay Certification Registry Recommendation Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-208 installed")
    print()
    print("Run:")
    print("py test_oi_208_universal_market_adapter_replay_certification_registry_recommendation_engine.py")


if __name__ == "__main__":
    main()