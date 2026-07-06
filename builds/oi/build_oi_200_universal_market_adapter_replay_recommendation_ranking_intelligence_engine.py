from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_recommendation_ranking_intelligence_engine.py"
TEST = ROOT / "test_oi_200_universal_market_adapter_replay_recommendation_ranking_intelligence_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
"""
OI-200 — Oracle Universal Market Adapter Replay Recommendation Ranking Intelligence Engine

Read-only Oracle Intelligence component.

Consumes OI-199 ranking analytics and converts analytics findings into
institutional replay intelligence signals.

Oracle is the Brain.
Q Series is the Hand.
Oracle never executes, routes orders, or manages positions.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Tuple


ENGINE_ID = "OI-200"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Recommendation Ranking Intelligence Engine"
ENGINE_VERSION = "1.0.1"


@dataclass(frozen=True)
class ReplayRankingIntelligenceSignal:
    signal_id: str
    category: str
    severity: str
    score: float
    title: str
    explanation: str
    recommendation: str
    supporting_findings: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["supporting_findings"] = list(self.supporting_findings)
        return data


@dataclass(frozen=True)
class ReplayRankingIntelligenceResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    signal_count: int
    intelligence_score: float
    signals: Tuple[ReplayRankingIntelligenceSignal, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "signal_count": self.signal_count,
            "intelligence_score": self.intelligence_score,
            "signals": [signal.to_dict() for signal in self.signals],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine:
    """
    Converts analytics findings into read-only intelligence.

    Scoring contract:
        baseline: 0.50
        positive finding: +0.12
        info finding: +0.02
        warning finding: -0.10
        empty input: remains 0.50 and status review
    """

    def evaluate(self, analytics: Any) -> ReplayRankingIntelligenceResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        findings = self._extract_findings(analytics)

        intelligence_score = 0.50
        signals: List[ReplayRankingIntelligenceSignal] = []

        for finding in findings:
            finding_id = str(finding.get("finding_id", "UNKNOWN_FINDING"))
            severity = str(finding.get("severity", "info")).lower().strip()
            title = str(finding.get("title", finding_id))
            detail = str(finding.get("detail", ""))
            recommendation = str(finding.get("recommendation", ""))

            if severity == "positive":
                intelligence_score += 0.12
                category = "strength"
                signal_score = 0.90
            elif severity == "warning":
                intelligence_score -= 0.10
                category = "risk"
                signal_score = 0.35
            else:
                intelligence_score += 0.02
                severity = "info"
                category = "context"
                signal_score = 0.60

            signals.append(
                ReplayRankingIntelligenceSignal(
                    signal_id=f"SIG_{finding_id}",
                    category=category,
                    severity=severity,
                    score=signal_score,
                    title=title,
                    explanation=detail,
                    recommendation=recommendation,
                    supporting_findings=(finding_id,),
                )
            )

        intelligence_score = round(max(0.0, min(1.0, intelligence_score)), 6)
        status = self._status(intelligence_score, signals)

        explanation = (
            f"Converted {len(findings)} replay ranking analytics finding(s) into "
            f"{len(signals)} read-only intelligence signal(s). Intelligence score is "
            f"{intelligence_score}. Oracle remains advisory only; Q Series remains "
            "the exclusive execution engine."
        )

        return ReplayRankingIntelligenceResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            signal_count=len(signals),
            intelligence_score=intelligence_score,
            signals=tuple(signals),
            telemetry=self._telemetry(analytics, len(findings), len(signals)),
            explanation=explanation,
        )

    def _status(self, score: float, signals: List[ReplayRankingIntelligenceSignal]) -> str:
        if not signals:
            return "review"
        if any(signal.severity == "warning" for signal in signals) and score < 0.60:
            return "review"
        if score >= 0.80:
            return "strong"
        if score >= 0.60:
            return "good"
        if score >= 0.40:
            return "review"
        return "weak"

    def _extract_findings(self, analytics: Any) -> List[Dict[str, Any]]:
        if analytics is None:
            return []

        if isinstance(analytics, Mapping):
            raw = analytics.get("findings", [])
        elif hasattr(analytics, "findings"):
            raw = getattr(analytics, "findings")
        else:
            raw = []

        if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
            return []

        findings: List[Dict[str, Any]] = []
        for item in raw:
            mapped = self._to_mapping(item)
            if mapped:
                findings.append(mapped)
        return findings

    def _telemetry(self, analytics: Any, findings_count: int, signals_count: int) -> Dict[str, Any]:
        analytics_map = self._to_mapping(analytics)
        return {
            "engine_id": ENGINE_ID,
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "read_only": True,
            "oracle_role": "brain",
            "execution_owner": "Q Series",
            "does_not_execute": True,
            "does_not_route_orders": True,
            "does_not_manage_positions": True,
            "input_engine_id": analytics_map.get("engine_id"),
            "canonical_input": "ReplayRecommendationRankingAnalyticsResult compatible",
            "canonical_output": "ReplayRankingIntelligenceResult",
            "findings_count": findings_count,
            "signals_count": signals_count,
            "explainability": True,
            "replayability": True,
        }

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


def evaluate_replay_recommendation_ranking_intelligence(
    analytics: Any,
) -> ReplayRankingIntelligenceResult:
    return UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine().evaluate(analytics)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayRankingIntelligenceSignal",
    "ReplayRankingIntelligenceResult",
    "UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine",
    "evaluate_replay_recommendation_ranking_intelligence",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_intelligence_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine,
    evaluate_replay_recommendation_ranking_intelligence,
)


def test_positive_and_info_findings_produce_good_status():
    analytics = {
        "engine_id": "OI-199",
        "findings": [
            {
                "finding_id": "OI199_STRONG_AVERAGE_SCORE",
                "severity": "positive",
                "title": "Strong average ranking score.",
                "detail": "Average ranking score is strong.",
                "recommendation": "Continue replay monitoring.",
            },
            {
                "finding_id": "OI199_HIGH_PRIORITY_CLUSTER",
                "severity": "info",
                "title": "High priority cluster.",
                "detail": "High-priority rankings detected.",
                "recommendation": "Review cluster for bias.",
            },
        ],
    }

    result = UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine().evaluate(analytics)

    assert result.engine_id == ENGINE_ID
    assert result.signal_count == 2
    assert result.intelligence_score == 0.64
    assert result.status == "good"
    assert result.signals[0].category == "strength"
    assert result.signals[1].category == "context"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert result.telemetry["input_engine_id"] == "OI-199"


def test_warning_findings_trigger_review():
    analytics = {
        "engine_id": "OI-199",
        "findings": [
            {
                "finding_id": "OI199_READ_ONLY_TELEMETRY_GAP",
                "severity": "warning",
                "title": "Read-only telemetry gap detected.",
                "detail": "Some rankings did not carry read-only telemetry.",
                "recommendation": "Repair upstream telemetry.",
            }
        ],
    }

    result = evaluate_replay_recommendation_ranking_intelligence(analytics)

    assert result.signal_count == 1
    assert result.intelligence_score == 0.40
    assert result.status == "review"
    assert result.signals[0].category == "risk"
    assert result.signals[0].severity == "warning"


def test_empty_input_is_safe_and_read_only():
    result = UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine().evaluate(
        {"engine_id": "OI-199", "findings": []}
    )

    assert result.signal_count == 0
    assert result.intelligence_score == 0.50
    assert result.status == "review"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_positive_and_info_findings_produce_good_status()
    test_warning_findings_trigger_review()
    test_empty_input_is_safe_and_read_only()

    print("[PASS] OI-200 Universal Market Adapter Replay Recommendation Ranking Intelligence Engine")
    print(
        evaluate_replay_recommendation_ranking_intelligence(
            {
                "engine_id": "OI-199",
                "findings": [
                    {
                        "finding_id": "DEMO_POSITIVE",
                        "severity": "positive",
                        "title": "Demo positive replay ranking intelligence.",
                        "detail": "The ranked replay recommendation analytics show constructive replay evidence.",
                        "recommendation": "Forward to read-only Oracle certification review.",
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
        "from .universal_market_adapter_replay_recommendation_ranking_intelligence_engine import "
        "UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine, "
        "evaluate_replay_recommendation_ranking_intelligence\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-200 INSTALLER")
    print(" Universal Market Adapter Replay Recommendation Ranking Intelligence Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-200 installed")
    print()
    print("Run:")
    print("py test_oi_200_universal_market_adapter_replay_recommendation_ranking_intelligence_engine.py")


if __name__ == "__main__":
    main()