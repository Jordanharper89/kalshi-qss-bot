from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_recommendation_ranking_certification_engine.py"
TEST = ROOT / "test_oi_201_universal_market_adapter_replay_recommendation_ranking_certification_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
"""
OI-201 — Oracle Universal Market Adapter Replay Recommendation Ranking Certification Engine

Read-only Oracle Intelligence component.

Consumes OI-200 replay ranking intelligence output and produces read-only
certification decisions for downstream Oracle review.

Oracle certifies intelligence quality.
Q Series remains the only execution engine.
This module never executes, routes orders, or manages positions.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Tuple


ENGINE_ID = "OI-201"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Recommendation Ranking Certification Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ReplayRankingCertificationDecision:
    decision_id: str
    recommendation: str
    certified: bool
    certification_level: str
    confidence: float
    reason_codes: Tuple[str, ...] = field(default_factory=tuple)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        return data


@dataclass(frozen=True)
class ReplayRankingCertificationResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    certified: bool
    certification_level: str
    intelligence_score: float
    signal_count: int
    decisions: Tuple[ReplayRankingCertificationDecision, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "certified": self.certified,
            "certification_level": self.certification_level,
            "intelligence_score": self.intelligence_score,
            "signal_count": self.signal_count,
            "decisions": [decision.to_dict() for decision in self.decisions],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayRecommendationRankingCertificationEngine:
    """
    Converts replay ranking intelligence into read-only certification.

    Certification rules:
        - strong_certified: score >= 0.80 and no warning signals
        - certified: score >= 0.60 and no warning signals
        - review_required: score >= 0.40 or any warning signal
        - rejected: score < 0.40

    Certification is advisory only. It does not trigger execution.
    """

    def certify(self, intelligence: Any) -> ReplayRankingCertificationResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        intelligence_map = self._to_mapping(intelligence)

        score = self._clamp01(self._number(intelligence_map, "intelligence_score", default=0.0))
        status_text = str(intelligence_map.get("status", "unknown")).lower()
        signals = self._extract_signals(intelligence_map)

        warning_count = sum(1 for signal in signals if str(signal.get("severity", "")).lower() == "warning")
        strength_count = sum(1 for signal in signals if str(signal.get("category", "")).lower() == "strength")
        risk_count = sum(1 for signal in signals if str(signal.get("category", "")).lower() == "risk")

        certified = False
        certification_level = "uncertified"
        status = "review"
        reason_codes: List[str] = [
            "READ_ONLY_ORACLE_CERTIFICATION",
            "Q_SERIES_EXECUTION_REQUIRED",
        ]

        if not signals:
            certification_level = "review_required"
            status = "review"
            reason_codes.append("NO_INTELLIGENCE_SIGNALS")
        elif score >= 0.80 and warning_count == 0:
            certified = True
            certification_level = "strong_certified"
            status = "certified"
            reason_codes.append("STRONG_INTELLIGENCE_SCORE")
            reason_codes.append("NO_WARNING_SIGNALS")
        elif score >= 0.60 and warning_count == 0:
            certified = True
            certification_level = "certified"
            status = "certified"
            reason_codes.append("PASSING_INTELLIGENCE_SCORE")
            reason_codes.append("NO_WARNING_SIGNALS")
        elif score >= 0.40:
            certification_level = "review_required"
            status = "review"
            reason_codes.append("REVIEW_LEVEL_INTELLIGENCE_SCORE")
            if warning_count:
                reason_codes.append("WARNING_SIGNALS_PRESENT")
        else:
            certification_level = "rejected"
            status = "rejected"
            reason_codes.append("WEAK_INTELLIGENCE_SCORE")

        if warning_count:
            reason_codes.append("CERTIFICATION_RISK_PRESENT")
        if strength_count:
            reason_codes.append("STRENGTH_SIGNALS_PRESENT")
        if risk_count:
            reason_codes.append("RISK_SIGNALS_PRESENT")
        if status_text:
            reason_codes.append(f"INPUT_STATUS_{status_text.upper()}")

        decision = ReplayRankingCertificationDecision(
            decision_id="OI201_REPLAY_RANKING_CERTIFICATION_DECISION",
            recommendation=self._recommendation_for_level(certification_level),
            certified=certified,
            certification_level=certification_level,
            confidence=score,
            reason_codes=tuple(reason_codes),
            explanation=(
                f"Replay ranking intelligence score {score:.4f} with "
                f"{len(signals)} signal(s), {warning_count} warning signal(s), "
                f"{strength_count} strength signal(s), and {risk_count} risk signal(s). "
                "Certification is read-only and advisory. Q Series remains the only execution engine."
            ),
        )

        explanation = (
            f"OI-201 produced {certification_level} certification with status {status}. "
            f"Certified={certified}. Intelligence score={score:.4f}. "
            "Oracle certification does not execute, route orders, or manage positions."
        )

        return ReplayRankingCertificationResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            certified=certified,
            certification_level=certification_level,
            intelligence_score=score,
            signal_count=len(signals),
            decisions=(decision,),
            telemetry=self._telemetry(
                intelligence_map=intelligence_map,
                signals_count=len(signals),
                warning_count=warning_count,
                strength_count=strength_count,
                risk_count=risk_count,
            ),
            explanation=explanation,
        )

    def _recommendation_for_level(self, certification_level: str) -> str:
        if certification_level == "strong_certified":
            return "Promote to downstream read-only Oracle review as a strong certification candidate."
        if certification_level == "certified":
            return "Promote to downstream read-only Oracle review as a certified candidate."
        if certification_level == "review_required":
            return "Hold for additional Oracle review before any downstream certification promotion."
        if certification_level == "rejected":
            return "Do not promote. Require stronger replay intelligence before reconsideration."
        return "Hold for review."

    def _extract_signals(self, intelligence_map: Mapping[str, Any]) -> List[Dict[str, Any]]:
        raw = intelligence_map.get("signals", [])
        if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
            return []

        signals: List[Dict[str, Any]] = []
        for item in raw:
            mapped = self._to_mapping(item)
            if mapped:
                signals.append(mapped)
        return signals

    def _telemetry(
        self,
        *,
        intelligence_map: Mapping[str, Any],
        signals_count: int,
        warning_count: int,
        strength_count: int,
        risk_count: int,
    ) -> Dict[str, Any]:
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
            "input_engine_id": intelligence_map.get("engine_id"),
            "canonical_input": "ReplayRankingIntelligenceResult compatible",
            "canonical_output": "ReplayRankingCertificationResult",
            "signals_count": signals_count,
            "warning_count": warning_count,
            "strength_count": strength_count,
            "risk_count": risk_count,
            "explainability": True,
            "replayability": True,
            "certification_is_advisory": True,
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

    def _number(self, data: Mapping[str, Any], key: str, *, default: float = 0.0) -> float:
        value = data.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _clamp01(self, value: float) -> float:
        value = float(value)
        if value > 1.0 and value <= 100.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))


def certify_replay_recommendation_ranking_intelligence(
    intelligence: Any,
) -> ReplayRankingCertificationResult:
    return UniversalMarketAdapterReplayRecommendationRankingCertificationEngine().certify(intelligence)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayRankingCertificationDecision",
    "ReplayRankingCertificationResult",
    "UniversalMarketAdapterReplayRecommendationRankingCertificationEngine",
    "certify_replay_recommendation_ranking_intelligence",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_certification_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayRecommendationRankingCertificationEngine,
    certify_replay_recommendation_ranking_intelligence,
)


def test_certifies_good_intelligence_without_warning_signals():
    intelligence = {
        "engine_id": "OI-200",
        "status": "good",
        "intelligence_score": 0.64,
        "signals": [
            {
                "signal_id": "SIG_POSITIVE",
                "category": "strength",
                "severity": "positive",
                "score": 0.90,
                "title": "Constructive replay intelligence.",
                "explanation": "Replay analytics are constructive.",
                "recommendation": "Promote to certification review.",
            },
            {
                "signal_id": "SIG_INFO",
                "category": "context",
                "severity": "info",
                "score": 0.60,
                "title": "Context signal.",
                "explanation": "Additional context exists.",
                "recommendation": "Review context.",
            },
        ],
    }

    result = UniversalMarketAdapterReplayRecommendationRankingCertificationEngine().certify(intelligence)

    assert result.engine_id == ENGINE_ID
    assert result.status == "certified"
    assert result.certified is True
    assert result.certification_level == "certified"
    assert result.intelligence_score == 0.64
    assert result.signal_count == 2
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert result.telemetry["input_engine_id"] == "OI-200"
    assert result.decisions[0].certified is True
    assert "READ_ONLY_ORACLE_CERTIFICATION" in result.decisions[0].reason_codes
    assert "Q_SERIES_EXECUTION_REQUIRED" in result.decisions[0].reason_codes

def test_warning_signal_requires_review():
    intelligence = {
        "engine_id": "OI-200",
        "status": "review",
        "intelligence_score": 0.40,
        "signals": [
            {
                "signal_id": "SIG_WARNING",
                "category": "risk",
                "severity": "warning",
                "score": 0.35,
                "title": "Telemetry gap.",
                "explanation": "Read-only telemetry gap detected.",
                "recommendation": "Repair upstream telemetry.",
            }
        ],
    }

    result = certify_replay_recommendation_ranking_intelligence(intelligence)

    assert result.status == "review"
    assert result.certified is False
    assert result.certification_level == "review_required"
    assert result.signal_count == 1
    assert result.telemetry["warning_count"] == 1
    assert "WARNING_SIGNALS_PRESENT" in result.decisions[0].reason_codes


def test_empty_intelligence_is_safe_and_not_certified():
    result = UniversalMarketAdapterReplayRecommendationRankingCertificationEngine().certify(
        {
            "engine_id": "OI-200",
            "status": "review",
            "intelligence_score": 0.50,
            "signals": [],
        }
    )

    assert result.status == "review"
    assert result.certified is False
    assert result.certification_level == "review_required"
    assert result.signal_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True
    assert "NO_INTELLIGENCE_SIGNALS" in result.decisions[0].reason_codes


if __name__ == "__main__":
    test_certifies_good_intelligence_without_warning_signals()
    test_warning_signal_requires_review()
    test_empty_intelligence_is_safe_and_not_certified()

    print("[PASS] OI-201 Universal Market Adapter Replay Recommendation Ranking Certification Engine")
    print(
        certify_replay_recommendation_ranking_intelligence(
            {
                "engine_id": "OI-200",
                "status": "good",
                "intelligence_score": 0.64,
                "signals": [
                    {
                        "signal_id": "SIG_DEMO",
                        "category": "strength",
                        "severity": "positive",
                        "score": 0.90,
                        "title": "Demo replay ranking intelligence.",
                        "explanation": "Replay ranking intelligence is constructive.",
                        "recommendation": "Promote to read-only Oracle certification review.",
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
        "from .universal_market_adapter_replay_recommendation_ranking_certification_engine import "
        "UniversalMarketAdapterReplayRecommendationRankingCertificationEngine, "
        "certify_replay_recommendation_ranking_intelligence\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-201 INSTALLER")
    print(" Universal Market Adapter Replay Recommendation Ranking Certification Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-201 installed")
    print()
    print("Run:")
    print("py test_oi_201_universal_market_adapter_replay_recommendation_ranking_certification_engine.py")


if __name__ == "__main__":
    main()