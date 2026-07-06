from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_recommendation_ranking_analytics_engine.py"
TEST = ROOT / "test_oi_199_universal_market_adapter_replay_recommendation_ranking_analytics_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
"""
OI-199 — Oracle Universal Market Adapter Replay Recommendation Ranking Analytics Engine

Read-only Oracle Intelligence component.

Purpose:
    Analyze ranked replay recommendation outputs produced by OI-198.

This engine does not rank candidates itself. It evaluates already-ranked replay
recommendations and produces institutional analytics about quality distribution,
priority distribution, grade concentration, score spread, confidence spread,
reason-code frequency, telemetry coverage, advisory safety, and replay-readiness.

Architecture:
    - Oracle is the Brain.
    - Q Series is the Hand.
    - Oracle remains permanently read-only.
    - Q Series remains the only execution engine.
    - This module never submits, routes, manages, modifies, or executes orders.
    - Output is deterministic, explainable, replayable, and telemetry-ready.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


ENGINE_ID = "OI-199"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Recommendation Ranking Analytics Engine"
ENGINE_VERSION = "1.0.0"


GRADE_ORDER = {
    "A+": 7,
    "A": 6,
    "A-": 5,
    "B+": 4,
    "B": 3,
    "C": 2,
    "D": 1,
    "UNKNOWN": 0,
}


@dataclass(frozen=True)
class ReplayRankingAnalyticsBucket:
    name: str
    count: int
    percentage: float
    members: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["members"] = list(self.members)
        return data


@dataclass(frozen=True)
class ReplayRankingAnalyticsFinding:
    finding_id: str
    severity: str
    title: str
    detail: str
    recommendation: str
    reason_codes: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        return data


@dataclass(frozen=True)
class ReplayRecommendationRankingAnalyticsResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    input_count: int
    analyzed_count: int
    score_summary: Dict[str, Any]
    confidence_summary: Dict[str, Any]
    grade_distribution: Tuple[ReplayRankingAnalyticsBucket, ...]
    priority_distribution: Tuple[ReplayRankingAnalyticsBucket, ...]
    adapter_distribution: Tuple[ReplayRankingAnalyticsBucket, ...]
    reason_code_distribution: Tuple[ReplayRankingAnalyticsBucket, ...]
    findings: Tuple[ReplayRankingAnalyticsFinding, ...]
    telemetry: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "input_count": self.input_count,
            "analyzed_count": self.analyzed_count,
            "score_summary": dict(self.score_summary),
            "confidence_summary": dict(self.confidence_summary),
            "grade_distribution": [bucket.to_dict() for bucket in self.grade_distribution],
            "priority_distribution": [bucket.to_dict() for bucket in self.priority_distribution],
            "adapter_distribution": [bucket.to_dict() for bucket in self.adapter_distribution],
            "reason_code_distribution": [bucket.to_dict() for bucket in self.reason_code_distribution],
            "findings": [finding.to_dict() for finding in self.findings],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine:
    """
    Analytics engine for ranked replay recommendation output.

    Input may be:
        - ReplayRecommendationRankingResult-like object with .rankings
        - dictionary with "rankings"
        - iterable of RankedReplayRecommendation-like objects
        - iterable of dictionaries

    Output is the canonical OI-199 analytics result.
    """

    def analyze(self, ranking_output: Any) -> ReplayRecommendationRankingAnalyticsResult:
        generated_at = datetime.now(timezone.utc).isoformat()

        records = self._extract_rankings(ranking_output)
        normalized = [record for record in (self._normalize_record(item) for item in records) if record]

        if not normalized:
            return ReplayRecommendationRankingAnalyticsResult(
                engine_id=ENGINE_ID,
                engine_name=ENGINE_NAME,
                engine_version=ENGINE_VERSION,
                generated_at=generated_at,
                status="empty",
                input_count=len(records),
                analyzed_count=0,
                score_summary=self._empty_summary("score"),
                confidence_summary=self._empty_summary("confidence"),
                grade_distribution=tuple(),
                priority_distribution=tuple(),
                adapter_distribution=tuple(),
                reason_code_distribution=tuple(),
                findings=(
                    ReplayRankingAnalyticsFinding(
                        finding_id="OI199_EMPTY_INPUT",
                        severity="info",
                        title="No ranked replay recommendations were available.",
                        detail="The analytics engine received no usable ranking records.",
                        recommendation="Confirm that OI-198 produced ranked recommendations before analytics are requested.",
                        reason_codes=("NO_USABLE_RANKINGS", "READ_ONLY_ANALYTICS"),
                    ),
                ),
                telemetry=self._base_telemetry(extra={"empty": True}),
                explanation=(
                    "No replay recommendation ranking records were available for analytics. "
                    "Oracle remains read-only and no execution action was taken."
                ),
            )

        score_summary = self._numeric_summary(normalized, "score")
        confidence_summary = self._numeric_summary(normalized, "confidence")

        grade_distribution = self._bucket_distribution(normalized, "grade")
        priority_distribution = self._bucket_distribution(normalized, "priority")
        adapter_distribution = self._bucket_distribution(normalized, "adapter_id")
        reason_code_distribution = self._reason_code_distribution(normalized)

        findings = self._generate_findings(
            normalized=normalized,
            score_summary=score_summary,
            confidence_summary=confidence_summary,
            grade_distribution=grade_distribution,
            priority_distribution=priority_distribution,
            reason_code_distribution=reason_code_distribution,
        )

        status = self._status_from_findings(findings)
        explanation = self._explain(
            normalized=normalized,
            score_summary=score_summary,
            confidence_summary=confidence_summary,
            findings=findings,
        )

        return ReplayRecommendationRankingAnalyticsResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            input_count=len(records),
            analyzed_count=len(normalized),
            score_summary=score_summary,
            confidence_summary=confidence_summary,
            grade_distribution=grade_distribution,
            priority_distribution=priority_distribution,
            adapter_distribution=adapter_distribution,
            reason_code_distribution=reason_code_distribution,
            findings=tuple(findings),
            telemetry=self._base_telemetry(
                extra={
                    "empty": False,
                    "canonical_input": "ReplayRecommendationRankingResult compatible",
                    "canonical_output": "ReplayRecommendationRankingAnalyticsResult",
                    "read_only_verified": True,
                    "execution_blocked": True,
                }
            ),
            explanation=explanation,
        )

    def _extract_rankings(self, ranking_output: Any) -> List[Any]:
        if ranking_output is None:
            return []

        if isinstance(ranking_output, Mapping):
            rankings = ranking_output.get("rankings", [])
            if isinstance(rankings, list):
                return list(rankings)
            if isinstance(rankings, tuple):
                return list(rankings)
            return []

        if hasattr(ranking_output, "rankings"):
            rankings = getattr(ranking_output, "rankings")
            if isinstance(rankings, (list, tuple)):
                return list(rankings)

        if isinstance(ranking_output, Iterable) and not isinstance(ranking_output, (str, bytes)):
            return list(ranking_output)

        return []

    def _normalize_record(self, item: Any) -> Optional[Dict[str, Any]]:
        data = self._to_mapping(item)
        if not data:
            return None

        recommendation_id = self._text(data, "recommendation_id", "id", default="")
        market_id = self._text(data, "market_id", "market", "ticker", default="")
        adapter_id = self._text(data, "adapter_id", "adapter", default="unknown_adapter")
        grade = self._text(data, "grade", default="UNKNOWN").upper()
        priority = self._text(data, "priority", default="watch").lower()
        explanation = self._text(data, "explanation", default="")

        score = self._number(data, "score", default=0.0)
        confidence = self._number(data, "confidence", default=0.0)
        rank = int(self._number(data, "rank", default=0.0))

        reason_codes = data.get("reason_codes", [])
        if isinstance(reason_codes, str):
            reason_codes = [reason_codes]
        elif isinstance(reason_codes, tuple):
            reason_codes = list(reason_codes)
        elif not isinstance(reason_codes, list):
            reason_codes = []

        telemetry = data.get("telemetry", {})
        if not isinstance(telemetry, Mapping):
            telemetry = {}

        source = data.get("source", {})
        if not isinstance(source, Mapping):
            source = {}

        return {
            "rank": rank,
            "recommendation_id": recommendation_id or f"unknown_recommendation_{rank}",
            "market_id": market_id or "unknown_market",
            "adapter_id": adapter_id or "unknown_adapter",
            "score": self._clamp01(score),
            "grade": grade if grade in GRADE_ORDER else "UNKNOWN",
            "confidence": self._clamp01(confidence),
            "priority": priority or "watch",
            "reason_codes": [str(code) for code in reason_codes if str(code).strip()],
            "explanation": explanation,
            "telemetry": dict(telemetry),
            "source": dict(source),
        }

    def _numeric_summary(self, records: Sequence[Mapping[str, Any]], field: str) -> Dict[str, Any]:
        values = [float(record[field]) for record in records]
        if not values:
            return self._empty_summary(field)

        sorted_values = sorted(values)
        return {
            "field": field,
            "count": len(values),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "mean": round(mean(values), 6),
            "median": round(median(values), 6),
            "spread": round(max(values) - min(values), 6),
            "top": round(sorted_values[-1], 6),
            "bottom": round(sorted_values[0], 6),
        }

    def _empty_summary(self, field: str) -> Dict[str, Any]:
        return {
            "field": field,
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "spread": None,
            "top": None,
            "bottom": None,
        }

    def _bucket_distribution(
        self,
        records: Sequence[Mapping[str, Any]],
        field: str,
    ) -> Tuple[ReplayRankingAnalyticsBucket, ...]:
        total = len(records)
        buckets: Dict[str, List[str]] = {}

        for record in records:
            name = str(record.get(field, "UNKNOWN") or "UNKNOWN")
            member = str(record.get("recommendation_id", "unknown"))
            buckets.setdefault(name, []).append(member)

        output: List[ReplayRankingAnalyticsBucket] = []
        for name, members in sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0])):
            output.append(
                ReplayRankingAnalyticsBucket(
                    name=name,
                    count=len(members),
                    percentage=round((len(members) / total) * 100.0, 6) if total else 0.0,
                    members=tuple(members),
                )
            )

        return tuple(output)

    def _reason_code_distribution(
        self,
        records: Sequence[Mapping[str, Any]],
    ) -> Tuple[ReplayRankingAnalyticsBucket, ...]:
        total = len(records)
        buckets: Dict[str, List[str]] = {}

        for record in records:
            member = str(record.get("recommendation_id", "unknown"))
            for code in record.get("reason_codes", []):
                buckets.setdefault(str(code), []).append(member)

        output: List[ReplayRankingAnalyticsBucket] = []
        for name, members in sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0])):
            output.append(
                ReplayRankingAnalyticsBucket(
                    name=name,
                    count=len(members),
                    percentage=round((len(members) / total) * 100.0, 6) if total else 0.0,
                    members=tuple(members),
                )
            )

        return tuple(output)

    def _generate_findings(
        self,
        *,
        normalized: Sequence[Mapping[str, Any]],
        score_summary: Mapping[str, Any],
        confidence_summary: Mapping[str, Any],
        grade_distribution: Sequence[ReplayRankingAnalyticsBucket],
        priority_distribution: Sequence[ReplayRankingAnalyticsBucket],
        reason_code_distribution: Sequence[ReplayRankingAnalyticsBucket],
    ) -> List[ReplayRankingAnalyticsFinding]:
        findings: List[ReplayRankingAnalyticsFinding] = []

        avg_score = float(score_summary.get("mean") or 0.0)
        avg_confidence = float(confidence_summary.get("mean") or 0.0)
        score_spread = float(score_summary.get("spread") or 0.0)

        high_grade_count = sum(
            1 for item in normalized if GRADE_ORDER.get(str(item.get("grade", "UNKNOWN")), 0) >= GRADE_ORDER["A-"]
        )
        high_grade_pct = (high_grade_count / len(normalized)) * 100.0 if normalized else 0.0

        high_priority_count = sum(1 for item in normalized if item.get("priority") == "high")
        high_priority_pct = (high_priority_count / len(normalized)) * 100.0 if normalized else 0.0

        read_only_count = sum(
            1
            for item in normalized
            if "READ_ONLY_ORACLE_RECOMMENDATION" in item.get("reason_codes", [])
            or item.get("telemetry", {}).get("read_only") is True
        )
        qseries_count = sum(
            1
            for item in normalized
            if "Q_SERIES_EXECUTION_REQUIRED" in item.get("reason_codes", [])
            or item.get("telemetry", {}).get("execution_owner") == "Q Series"
        )

        if avg_score >= 0.80:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_STRONG_AVERAGE_SCORE",
                    severity="positive",
                    title="Strong average ranking score.",
                    detail=f"Average ranking score is {avg_score:.4f}, indicating strong replay recommendation quality.",
                    recommendation="Continue replay monitoring and route advisory output to downstream Oracle certification layers.",
                    reason_codes=("STRONG_SCORE_DISTRIBUTION", "READ_ONLY_ANALYTICS"),
                )
            )
        elif avg_score < 0.55:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_WEAK_AVERAGE_SCORE",
                    severity="warning",
                    title="Weak average ranking score.",
                    detail=f"Average ranking score is {avg_score:.4f}, below institutional replay quality preference.",
                    recommendation="Do not elevate these recommendations without additional Oracle review.",
                    reason_codes=("WEAK_SCORE_DISTRIBUTION", "REQUIRES_MORE_REPLAY_SUPPORT"),
                )
            )

        if avg_confidence >= 0.80:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_STRONG_AVERAGE_CONFIDENCE",
                    severity="positive",
                    title="Strong average confidence.",
                    detail=f"Average confidence is {avg_confidence:.4f}.",
                    recommendation="Treat ranked recommendations as analytically mature, while preserving read-only Oracle boundaries.",
                    reason_codes=("STRONG_CONFIDENCE_DISTRIBUTION",),
                )
            )
        elif avg_confidence < 0.55:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_LOW_AVERAGE_CONFIDENCE",
                    severity="warning",
                    title="Low average confidence.",
                    detail=f"Average confidence is {avg_confidence:.4f}.",
                    recommendation="Require additional replay evidence before certification.",
                    reason_codes=("LOW_CONFIDENCE_DISTRIBUTION",),
                )
            )

        if score_spread >= 0.35:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_WIDE_SCORE_SPREAD",
                    severity="info",
                    title="Wide score spread detected.",
                    detail=f"Score spread is {score_spread:.4f}, meaning ranked candidates are meaningfully separated.",
                    recommendation="Ranking separation is useful for prioritization, but downstream certification should still verify top candidates.",
                    reason_codes=("WIDE_SCORE_SPREAD",),
                )
            )
        elif score_spread <= 0.05 and len(normalized) > 1:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_NARROW_SCORE_SPREAD",
                    severity="info",
                    title="Narrow score spread detected.",
                    detail=f"Score spread is {score_spread:.4f}, meaning ranked candidates are closely clustered.",
                    recommendation="Use secondary Oracle signals before treating small rank differences as meaningful.",
                    reason_codes=("NARROW_SCORE_SPREAD",),
                )
            )

        if high_grade_pct >= 50.0:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_HIGH_GRADE_CONCENTRATION",
                    severity="positive",
                    title="High-grade replay recommendation concentration.",
                    detail=f"{high_grade_pct:.2f}% of analyzed rankings are A- or better.",
                    recommendation="Promote these recommendations to replay certification review, not execution.",
                    reason_codes=("HIGH_GRADE_CONCENTRATION", "ORACLE_CERTIFICATION_CANDIDATE"),
                )
            )

        if high_priority_pct >= 40.0:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_HIGH_PRIORITY_CLUSTER",
                    severity="info",
                    title="High-priority cluster detected.",
                    detail=f"{high_priority_pct:.2f}% of analyzed rankings are high priority.",
                    recommendation="Review high-priority cluster for shared adapter, market, or replay bias.",
                    reason_codes=("HIGH_PRIORITY_CLUSTER",),
                )
            )

        if read_only_count < len(normalized):
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_READ_ONLY_TELEMETRY_GAP",
                    severity="warning",
                    title="Read-only telemetry gap detected.",
                    detail="One or more ranked recommendations did not explicitly carry read-only Oracle telemetry or reason codes.",
                    recommendation="Ensure upstream ranking modules preserve Oracle read-only telemetry on every advisory output.",
                    reason_codes=("READ_ONLY_TELEMETRY_GAP",),
                )
            )

        if qseries_count < len(normalized):
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_EXECUTION_OWNER_TELEMETRY_GAP",
                    severity="warning",
                    title="Q Series execution ownership telemetry gap detected.",
                    detail="One or more ranked recommendations did not explicitly identify Q Series as execution owner.",
                    recommendation="Preserve the Oracle Brain / Q Series Hand boundary in all ranked recommendation outputs.",
                    reason_codes=("EXECUTION_OWNER_TELEMETRY_GAP",),
                )
            )

        if not reason_code_distribution:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_REASON_CODE_GAP",
                    severity="warning",
                    title="Reason code coverage gap.",
                    detail="No reason codes were found in the analyzed ranking records.",
                    recommendation="Require explainability reason codes before downstream certification.",
                    reason_codes=("NO_REASON_CODES", "EXPLAINABILITY_GAP"),
                )
            )

        if not findings:
            findings.append(
                ReplayRankingAnalyticsFinding(
                    finding_id="OI199_STABLE_ANALYTICS_BASELINE",
                    severity="info",
                    title="Stable replay ranking analytics baseline.",
                    detail="No severe analytics issues were detected.",
                    recommendation="Continue monitoring ranking quality through replay analytics gates.",
                    reason_codes=("STABLE_BASELINE", "READ_ONLY_ANALYTICS"),
                )
            )

        return findings

    def _status_from_findings(self, findings: Sequence[ReplayRankingAnalyticsFinding]) -> str:
        if any(finding.severity == "warning" for finding in findings):
            return "review"
        return "ok"

    def _explain(
        self,
        *,
        normalized: Sequence[Mapping[str, Any]],
        score_summary: Mapping[str, Any],
        confidence_summary: Mapping[str, Any],
        findings: Sequence[ReplayRankingAnalyticsFinding],
    ) -> str:
        return (
            f"Analyzed {len(normalized)} replay recommendation ranking record(s). "
            f"Average score: {score_summary.get('mean')}. "
            f"Average confidence: {confidence_summary.get('mean')}. "
            f"Generated {len(findings)} analytics finding(s). "
            "Oracle output remains advisory and read-only; Q Series remains the only execution engine."
        )

    def _base_telemetry(self, *, extra: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        telemetry = {
            "engine_id": ENGINE_ID,
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "read_only": True,
            "oracle_role": "brain",
            "execution_owner": "Q Series",
            "does_not_execute": True,
            "does_not_route_orders": True,
            "does_not_manage_positions": True,
            "explainability": True,
            "replayability": True,
        }
        if extra:
            telemetry.update(dict(extra))
        return telemetry

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

    def _text(self, data: Mapping[str, Any], *keys: str, default: str = "") -> str:
        for key in keys:
            value = data.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return default

    def _number(self, data: Mapping[str, Any], *keys: str, default: float = 0.0) -> float:
        for key in keys:
            value = data.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return float(default)

    def _clamp01(self, value: float) -> float:
        value = float(value)
        if value > 1.0 and value <= 100.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))


def analyze_replay_recommendation_rankings(
    ranking_output: Any,
) -> ReplayRecommendationRankingAnalyticsResult:
    engine = UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine()
    return engine.analyze(ranking_output)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayRankingAnalyticsBucket",
    "ReplayRankingAnalyticsFinding",
    "ReplayRecommendationRankingAnalyticsResult",
    "UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine",
    "analyze_replay_recommendation_rankings",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_analytics_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine,
    analyze_replay_recommendation_rankings,
)


def test_analyzes_ranking_dict_output():
    ranking_output = {
        "rankings": [
            {
                "rank": 1,
                "recommendation_id": "strong",
                "market_id": "MARKET-A",
                "adapter_id": "adp.test",
                "score": 0.91,
                "grade": "A",
                "confidence": 0.93,
                "priority": "high",
                "reason_codes": [
                    "READ_ONLY_ORACLE_RECOMMENDATION",
                    "Q_SERIES_EXECUTION_REQUIRED",
                    "STRONG_CONFIDENCE",
                ],
                "telemetry": {
                    "read_only": True,
                    "execution_owner": "Q Series",
                },
            },
            {
                "rank": 2,
                "recommendation_id": "medium",
                "market_id": "MARKET-B",
                "adapter_id": "adp.test",
                "score": 0.74,
                "grade": "B+",
                "confidence": 0.77,
                "priority": "medium",
                "reason_codes": [
                    "READ_ONLY_ORACLE_RECOMMENDATION",
                    "Q_SERIES_EXECUTION_REQUIRED",
                ],
                "telemetry": {
                    "read_only": True,
                    "execution_owner": "Q Series",
                },
            },
        ]
    }

    engine = UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine()
    result = engine.analyze(ranking_output)

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.input_count == 2
    assert result.analyzed_count == 2
    assert result.score_summary["count"] == 2
    assert result.score_summary["max"] == 0.91
    assert result.confidence_summary["mean"] == 0.85
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert any(bucket.name == "adp.test" and bucket.count == 2 for bucket in result.adapter_distribution)
    assert any(finding.finding_id == "OI199_STRONG_AVERAGE_CONFIDENCE" for finding in result.findings)


def test_wrapper_accepts_iterable_rankings():
    rankings = [
        {
            "rank": 1,
            "recommendation_id": "one",
            "market_id": "M1",
            "adapter_id": "adp.one",
            "score": 88,
            "grade": "A",
            "confidence": 91,
            "priority": "high",
            "reason_codes": ["READ_ONLY_ORACLE_RECOMMENDATION", "Q_SERIES_EXECUTION_REQUIRED"],
            "telemetry": {"read_only": True, "execution_owner": "Q Series"},
        }
    ]

    result = analyze_replay_recommendation_rankings(rankings)

    assert result.status == "ok"
    assert result.analyzed_count == 1
    assert result.score_summary["mean"] == 0.88
    assert result.confidence_summary["mean"] == 0.91
    assert result.grade_distribution[0].name == "A"


def test_empty_input_is_safe():
    engine = UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine()
    result = engine.analyze([])

    assert result.status == "empty"
    assert result.input_count == 0
    assert result.analyzed_count == 0
    assert result.telemetry["read_only"] is True
    assert result.findings[0].finding_id == "OI199_EMPTY_INPUT"


if __name__ == "__main__":
    test_analyzes_ranking_dict_output()
    test_wrapper_accepts_iterable_rankings()
    test_empty_input_is_safe()

    print("[PASS] OI-199 Universal Market Adapter Replay Recommendation Ranking Analytics Engine")
    print(
        analyze_replay_recommendation_rankings(
            {
                "rankings": [
                    {
                        "rank": 1,
                        "recommendation_id": "demo",
                        "market_id": "DEMO-MARKET",
                        "adapter_id": "adp.demo",
                        "score": 0.86,
                        "grade": "A",
                        "confidence": 0.9,
                        "priority": "high",
                        "reason_codes": [
                            "READ_ONLY_ORACLE_RECOMMENDATION",
                            "Q_SERIES_EXECUTION_REQUIRED",
                            "STRONG_CONFIDENCE",
                        ],
                        "telemetry": {
                            "read_only": True,
                            "execution_owner": "Q Series",
                        },
                    }
                ]
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
        "from .universal_market_adapter_replay_recommendation_ranking_analytics_engine import "
        "UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine, "
        "analyze_replay_recommendation_rankings\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-199 INSTALLER")
    print(" Universal Market Adapter Replay Recommendation Ranking Analytics Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-199 installed")
    print()
    print("Run:")
    print("py test_oi_199_universal_market_adapter_replay_recommendation_ranking_analytics_engine.py")


if __name__ == "__main__":
    main()