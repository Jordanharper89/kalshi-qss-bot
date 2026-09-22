"""
OI-198 — Oracle Universal Market Adapter Replay Recommendation Ranking Engine

Read-only Oracle Intelligence component.

Purpose:
    Rank replay recommendation candidates produced by prior replay intelligence
    and recommendation modules.

Architecture:
    - Oracle is read-only.
    - Q Series owns execution.
    - This module never submits, routes, manages, or executes orders.
    - Ranking output is explainable, replayable, deterministic, and telemetry-ready.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


ENGINE_ID = "OI-198"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Recommendation Ranking Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RankedReplayRecommendation:
    rank: int
    recommendation_id: str
    market_id: str
    adapter_id: str
    score: float
    grade: str
    confidence: float
    priority: str
    reason_codes: Tuple[str, ...]
    explanation: str
    source: Dict[str, Any] = field(default_factory=dict)
    telemetry: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        return data


@dataclass(frozen=True)
class ReplayRecommendationRankingResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    ranked_count: int
    input_count: int
    rankings: Tuple[RankedReplayRecommendation, ...]
    telemetry: Dict[str, Any] = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "ranked_count": self.ranked_count,
            "input_count": self.input_count,
            "rankings": [item.to_dict() for item in self.rankings],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayRecommendationRankingEngine:
    """
    Deterministic read-only ranking engine for replay recommendations.

    The engine accepts dictionaries or objects with attributes. It is intentionally
    tolerant at the input boundary but strict in the output contract.
    """

    def __init__(
        self,
        *,
        confidence_weight: float = 0.30,
        edge_weight: float = 0.25,
        replay_weight: float = 0.20,
        stability_weight: float = 0.15,
        explainability_weight: float = 0.10,
    ) -> None:
        weights = {
            "confidence": confidence_weight,
            "edge": edge_weight,
            "replay": replay_weight,
            "stability": stability_weight,
            "explainability": explainability_weight,
        }
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Ranking weights must sum to a positive value.")

        self.weights = {key: value / total for key, value in weights.items()}

    def rank(
        self,
        recommendations: Iterable[Any],
        *,
        limit: Optional[int] = None,
        minimum_score: float = 0.0,
    ) -> ReplayRecommendationRankingResult:
        items = list(recommendations or [])
        generated_at = datetime.now(timezone.utc).isoformat()

        ranked_working: List[Dict[str, Any]] = []
        rejected_count = 0

        for index, candidate in enumerate(items):
            normalized = self._normalize_candidate(candidate, index=index)
            if normalized is None:
                rejected_count += 1
                continue

            score, score_parts = self._score_candidate(normalized)
            if score < minimum_score:
                rejected_count += 1
                continue

            normalized["score"] = score
            normalized["score_parts"] = score_parts
            ranked_working.append(normalized)

        ranked_working.sort(
            key=lambda item: (
                -item["score"],
                -item["confidence"],
                item["market_id"],
                item["recommendation_id"],
            )
        )

        if limit is not None:
            ranked_working = ranked_working[: max(0, int(limit))]

        rankings: List[RankedReplayRecommendation] = []
        for rank_index, item in enumerate(ranked_working, start=1):
            grade = self._grade(item["score"])
            priority = self._priority(item["score"], item["confidence"])
            reasons = self._reason_codes(item, grade, priority)
            explanation = self._explain(item, rank_index, grade, priority, reasons)

            rankings.append(
                RankedReplayRecommendation(
                    rank=rank_index,
                    recommendation_id=item["recommendation_id"],
                    market_id=item["market_id"],
                    adapter_id=item["adapter_id"],
                    score=round(item["score"], 6),
                    grade=grade,
                    confidence=round(item["confidence"], 6),
                    priority=priority,
                    reason_codes=tuple(reasons),
                    explanation=explanation,
                    source=dict(item["source"]),
                    telemetry={
                        "engine_id": ENGINE_ID,
                        "score_parts": dict(item["score_parts"]),
                        "read_only": True,
                        "execution_owner": "Q Series",
                        "oracle_role": "brain",
                    },
                )
            )

        status = "ok" if rankings else "empty"
        explanation = (
            f"Ranked {len(rankings)} replay recommendation candidate(s) from "
            f"{len(items)} input candidate(s). Oracle output is advisory only; "
            "Q Series remains the only execution engine."
        )

        return ReplayRecommendationRankingResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            ranked_count=len(rankings),
            input_count=len(items),
            rankings=tuple(rankings),
            telemetry={
                "read_only": True,
                "execution_owner": "Q Series",
                "oracle_role": "brain",
                "rejected_count": rejected_count,
                "weights": dict(self.weights),
                "canonical_output": "ReplayRecommendationRankingResult",
            },
            explanation=explanation,
        )

    def _normalize_candidate(self, candidate: Any, *, index: int) -> Optional[Dict[str, Any]]:
        data = self._to_mapping(candidate)
        if not data:
            return None

        market_id = self._first_text(data, "market_id", "market", "ticker", "event_ticker")
        adapter_id = self._first_text(data, "adapter_id", "adapter", "source_adapter")
        recommendation_id = self._first_text(data, "recommendation_id", "id", "signal_id")

        if not market_id:
            market_id = f"unknown_market_{index}"
        if not adapter_id:
            adapter_id = "unknown_adapter"
        if not recommendation_id:
            recommendation_id = self._stable_id(data, index)

        confidence = self._clamp01(self._first_number(data, "confidence", "confidence_score", default=0.0))
        edge = self._normalize_percent(self._first_number(data, "edge", "edge_pct", "expected_edge", default=0.0))
        replay_quality = self._clamp01(
            self._first_number(data, "replay_quality", "replay_score", "historical_score", default=confidence)
        )
        stability = self._clamp01(
            self._first_number(data, "stability", "stability_score", "consistency", default=0.5)
        )
        explainability = self._clamp01(
            self._first_number(data, "explainability", "explainability_score", default=0.5)
        )

        direction = self._first_text(data, "direction", "side", "recommendation", default="observe")
        rationale = self._first_text(data, "rationale", "explanation", "reason", default="No rationale supplied.")

        return {
            "recommendation_id": recommendation_id,
            "market_id": market_id,
            "adapter_id": adapter_id,
            "confidence": confidence,
            "edge": edge,
            "replay_quality": replay_quality,
            "stability": stability,
            "explainability": explainability,
            "direction": direction,
            "rationale": rationale,
            "source": dict(data),
        }

    def _score_candidate(self, item: Mapping[str, Any]) -> Tuple[float, Dict[str, float]]:
        parts = {
            "confidence": float(item["confidence"]) * self.weights["confidence"],
            "edge": float(item["edge"]) * self.weights["edge"],
            "replay": float(item["replay_quality"]) * self.weights["replay"],
            "stability": float(item["stability"]) * self.weights["stability"],
            "explainability": float(item["explainability"]) * self.weights["explainability"],
        }
        score = max(0.0, min(1.0, sum(parts.values())))
        return score, parts

    def _grade(self, score: float) -> str:
        if score >= 0.92:
            return "A+"
        if score >= 0.86:
            return "A"
        if score >= 0.80:
            return "A-"
        if score >= 0.72:
            return "B+"
        if score >= 0.64:
            return "B"
        if score >= 0.55:
            return "C"
        return "D"

    def _priority(self, score: float, confidence: float) -> str:
        if score >= 0.86 and confidence >= 0.80:
            return "high"
        if score >= 0.72 and confidence >= 0.65:
            return "medium"
        return "watch"

    def _reason_codes(
        self,
        item: Mapping[str, Any],
        grade: str,
        priority: str,
    ) -> List[str]:
        reasons = ["READ_ONLY_ORACLE_RECOMMENDATION", "Q_SERIES_EXECUTION_REQUIRED"]

        if grade in {"A+", "A", "A-"}:
            reasons.append("INSTITUTIONAL_GRADE_REPLAY_RANK")
        if priority == "high":
            reasons.append("HIGH_PRIORITY_REPLAY_CANDIDATE")
        if float(item["confidence"]) >= 0.80:
            reasons.append("STRONG_CONFIDENCE")
        if float(item["edge"]) >= 0.15:
            reasons.append("MATERIAL_EDGE")
        if float(item["replay_quality"]) >= 0.80:
            reasons.append("STRONG_REPLAY_SUPPORT")
        if float(item["stability"]) >= 0.75:
            reasons.append("STABLE_HISTORICAL_PATTERN")
        if float(item["explainability"]) >= 0.75:
            reasons.append("CLEAR_EXPLANATION_TRAIL")

        return reasons

    def _explain(
        self,
        item: Mapping[str, Any],
        rank: int,
        grade: str,
        priority: str,
        reasons: Sequence[str],
    ) -> str:
        return (
            f"Rank {rank}: recommendation {item['recommendation_id']} for market "
            f"{item['market_id']} via adapter {item['adapter_id']} received grade {grade} "
            f"with {priority} priority. Score was driven by confidence "
            f"{float(item['confidence']):.2f}, normalized edge {float(item['edge']):.2f}, "
            f"replay quality {float(item['replay_quality']):.2f}, stability "
            f"{float(item['stability']):.2f}, and explainability "
            f"{float(item['explainability']):.2f}. Reason codes: {', '.join(reasons)}. "
            "This is an Oracle advisory ranking only and does not execute trades."
        )

    def _to_mapping(self, candidate: Any) -> Dict[str, Any]:
        if candidate is None:
            return {}
        if isinstance(candidate, Mapping):
            return dict(candidate)
        if hasattr(candidate, "to_dict") and callable(candidate.to_dict):
            mapped = candidate.to_dict()
            if isinstance(mapped, Mapping):
                return dict(mapped)
        if hasattr(candidate, "__dict__"):
            return dict(vars(candidate))
        return {}

    def _first_text(self, data: Mapping[str, Any], *keys: str, default: str = "") -> str:
        for key in keys:
            value = data.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return default

    def _first_number(self, data: Mapping[str, Any], *keys: str, default: float = 0.0) -> float:
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
        if value > 1.0 and value <= 100.0:
            value = value / 100.0
        return max(0.0, min(1.0, float(value)))

    def _normalize_percent(self, value: float) -> float:
        value = float(value)
        if value > 1.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))

    def _stable_id(self, data: Mapping[str, Any], index: int) -> str:
        payload = repr(sorted((str(k), repr(v)) for k, v in data.items()))
        digest = sha256(payload.encode("utf-8")).hexdigest()[:12]
        return f"replay_recommendation_{index}_{digest}"


def rank_replay_recommendations(
    recommendations: Iterable[Any],
    *,
    limit: Optional[int] = None,
    minimum_score: float = 0.0,
) -> ReplayRecommendationRankingResult:
    engine = UniversalMarketAdapterReplayRecommendationRankingEngine()
    return engine.rank(recommendations, limit=limit, minimum_score=minimum_score)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "RankedReplayRecommendation",
    "ReplayRecommendationRankingResult",
    "UniversalMarketAdapterReplayRecommendationRankingEngine",
    "rank_replay_recommendations",
]
