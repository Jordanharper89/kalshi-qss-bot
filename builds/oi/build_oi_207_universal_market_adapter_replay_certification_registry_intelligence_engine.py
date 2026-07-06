from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_certification_registry_intelligence_engine.py"
TEST = ROOT / "test_oi_207_universal_market_adapter_replay_certification_registry_intelligence_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Tuple

ENGINE_ID = "OI-207"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Certification Registry Intelligence Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ReplayCertificationRegistryIntelligenceSignal:
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
class ReplayCertificationRegistryIntelligenceResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    intelligence_score: float
    signal_count: int
    signals: Tuple[ReplayCertificationRegistryIntelligenceSignal, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "intelligence_score": self.intelligence_score,
            "signal_count": self.signal_count,
            "signals": [signal.to_dict() for signal in self.signals],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayCertificationRegistryIntelligenceEngine:
    def evaluate(self, analytics: Any) -> ReplayCertificationRegistryIntelligenceResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        analytics_map = self._to_mapping(analytics)
        findings = self._extract_findings(analytics_map)

        intelligence_score = 0.50
        signals: List[ReplayCertificationRegistryIntelligenceSignal] = []

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
                intelligence_score -= 0.12
                category = "risk"
                signal_score = 0.30
            else:
                intelligence_score += 0.02
                severity = "info"
                category = "context"
                signal_score = 0.60

            signals.append(
                ReplayCertificationRegistryIntelligenceSignal(
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

        return ReplayCertificationRegistryIntelligenceResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            intelligence_score=intelligence_score,
            signal_count=len(signals),
            signals=tuple(signals),
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
                "input_engine_id": analytics_map.get("engine_id"),
                "canonical_input": "ReplayCertificationRegistryAnalyticsResult compatible",
                "canonical_output": "ReplayCertificationRegistryIntelligenceResult",
                "findings_count": len(findings),
                "signals_count": len(signals),
                "explainability": True,
                "replayability": True,
            },
            explanation=(
                f"Converted {len(findings)} replay certification registry analytics finding(s) "
                f"into {len(signals)} read-only intelligence signal(s). Intelligence score is "
                f"{intelligence_score}. Oracle remains advisory only; Q Series remains the only execution engine."
            ),
        )

    def _status(self, score: float, signals: List[ReplayCertificationRegistryIntelligenceSignal]) -> str:
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

    def _extract_findings(self, analytics_map: Mapping[str, Any]) -> List[Dict[str, Any]]:
        raw = analytics_map.get("findings", [])
        if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
            return []
        output: List[Dict[str, Any]] = []
        for item in raw:
            mapped = self._to_mapping(item)
            if mapped:
                output.append(mapped)
        return output

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


def evaluate_replay_certification_registry_intelligence(
    analytics: Any,
) -> ReplayCertificationRegistryIntelligenceResult:
    return UniversalMarketAdapterReplayCertificationRegistryIntelligenceEngine().evaluate(analytics)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayCertificationRegistryIntelligenceSignal",
    "ReplayCertificationRegistryIntelligenceResult",
    "UniversalMarketAdapterReplayCertificationRegistryIntelligenceEngine",
    "evaluate_replay_certification_registry_intelligence",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_intelligence_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryIntelligenceEngine,
    evaluate_replay_certification_registry_intelligence,
)


def test_positive_registry_analytics_produces_good_intelligence():
    analytics = {
        "engine_id": "OI-206",
        "findings": [
            {
                "finding_id": "OI206_CERTIFIED_COHORT_MAJORITY",
                "severity": "positive",
                "title": "Certified records are the majority.",
                "detail": "Most records are certified.",
                "recommendation": "Continue monitoring.",
            },
            {
                "finding_id": "OI206_REVIEW_STATUS_PRESENT",
                "severity": "info",
                "title": "Review records present.",
                "detail": "Some records require review.",
                "recommendation": "Inspect review records.",
            },
        ],
    }

    result = UniversalMarketAdapterReplayCertificationRegistryIntelligenceEngine().evaluate(analytics)

    assert result.engine_id == ENGINE_ID
    assert result.status == "good"
    assert result.intelligence_score == 0.64
    assert result.signal_count == 2
    assert result.signals[0].category == "strength"
    assert result.signals[1].category == "context"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert result.telemetry["input_engine_id"] == "OI-206"


def test_warning_registry_analytics_requires_review():
    result = evaluate_replay_certification_registry_intelligence(
        {
            "engine_id": "OI-206",
            "findings": [
                {
                    "finding_id": "OI206_WEAK_AVERAGE_CERTIFICATION_SCORE",
                    "severity": "warning",
                    "title": "Weak average score.",
                    "detail": "Average score is weak.",
                    "recommendation": "Hold for review.",
                }
            ],
        }
    )

    assert result.status == "review"
    assert result.intelligence_score == 0.38
    assert result.signal_count == 1
    assert result.signals[0].category == "risk"
    assert result.signals[0].severity == "warning"


def test_empty_analytics_is_safe_read_only():
    result = evaluate_replay_certification_registry_intelligence(
        {"engine_id": "OI-206", "findings": []}
    )

    assert result.status == "review"
    assert result.intelligence_score == 0.50
    assert result.signal_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_positive_registry_analytics_produces_good_intelligence()
    test_warning_registry_analytics_requires_review()
    test_empty_analytics_is_safe_read_only()

    print("[PASS] OI-207 Universal Market Adapter Replay Certification Registry Intelligence Engine")
    print(
        evaluate_replay_certification_registry_intelligence(
            {
                "engine_id": "OI-206",
                "findings": [
                    {
                        "finding_id": "DEMO_CERTIFIED_COHORT",
                        "severity": "positive",
                        "title": "Demo certified registry cohort.",
                        "detail": "The replay certification registry cohort is constructive.",
                        "recommendation": "Forward to read-only Oracle recommendation review.",
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
        "from .universal_market_adapter_replay_certification_registry_intelligence_engine import "
        "UniversalMarketAdapterReplayCertificationRegistryIntelligenceEngine, "
        "evaluate_replay_certification_registry_intelligence\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-207 INSTALLER")
    print(" Universal Market Adapter Replay Certification Registry Intelligence Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-207 installed")
    print()
    print("Run:")
    print("py test_oi_207_universal_market_adapter_replay_certification_registry_intelligence_engine.py")


if __name__ == "__main__":
    main()