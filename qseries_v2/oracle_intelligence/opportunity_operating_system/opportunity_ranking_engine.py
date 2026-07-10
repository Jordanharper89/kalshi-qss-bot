"""
OOS-002 Opportunity Ranking Engine

Ranks UniversalOpportunity objects across markets using deterministic,
explainable, profile-based scoring.

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional


OOS_RANKING_VERSION = "OOS-002"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RankingProfile(str, Enum):
    BALANCED = "balanced"
    MAX_EXPECTED_VALUE = "max_expected_value"
    LOWEST_RISK = "lowest_risk"
    FASTEST_SCALP = "fastest_scalp"
    HIGHEST_CONFIDENCE = "highest_confidence"
    CAPITAL_EFFICIENT = "capital_efficient"


PROFILE_WEIGHTS = {
    RankingProfile.BALANCED: {
        "confidence": 0.25,
        "edge": 0.22,
        "liquidity": 0.14,
        "freshness": 0.10,
        "urgency": 0.10,
        "risk": -0.10,
        "execution": -0.07,
        "capital": -0.02,
    },
    RankingProfile.MAX_EXPECTED_VALUE: {
        "confidence": 0.10,
        "edge": 0.68,
        "liquidity": 0.05,
        "freshness": 0.04,
        "urgency": 0.04,
        "risk": -0.04,
        "execution": -0.03,
        "capital": -0.02,
    },
    RankingProfile.LOWEST_RISK: {
        "confidence": 0.25,
        "edge": 0.14,
        "liquidity": 0.16,
        "freshness": 0.08,
        "urgency": 0.06,
        "risk": -0.23,
        "execution": -0.06,
        "capital": -0.02,
    },
    RankingProfile.FASTEST_SCALP: {
        "confidence": 0.20,
        "edge": 0.18,
        "liquidity": 0.16,
        "freshness": 0.16,
        "urgency": 0.18,
        "risk": -0.06,
        "execution": -0.05,
        "capital": -0.01,
    },
    RankingProfile.HIGHEST_CONFIDENCE: {
        "confidence": 0.45,
        "edge": 0.14,
        "liquidity": 0.12,
        "freshness": 0.08,
        "urgency": 0.06,
        "risk": -0.08,
        "execution": -0.05,
        "capital": -0.02,
    },
    RankingProfile.CAPITAL_EFFICIENT: {
        "confidence": 0.22,
        "edge": 0.22,
        "liquidity": 0.12,
        "freshness": 0.10,
        "urgency": 0.10,
        "risk": -0.08,
        "execution": -0.06,
        "capital": -0.10,
    },
}


@dataclass(frozen=True)
class RankingScoreBreakdown:
    confidence: float
    edge: float
    liquidity: float
    freshness: float
    urgency: float
    risk_penalty: float
    execution_penalty: float
    capital_penalty: float
    raw_score: float
    normalized_score: float
    profile: str
    schema_version: str = OOS_RANKING_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RankedOpportunity:
    rank: int
    opportunity: Any
    fingerprint: str
    score: float
    profile: str
    breakdown: RankingScoreBreakdown
    tie_breaker: str
    ranked_at: str = field(default_factory=utc_now)
    schema_version: str = OOS_RANKING_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        opp_to_dict = getattr(self.opportunity, "to_dict", None)
        opportunity_data = opp_to_dict() if callable(opp_to_dict) else self.opportunity

        return {
            "rank": self.rank,
            "opportunity": opportunity_data,
            "fingerprint": self.fingerprint,
            "score": self.score,
            "profile": self.profile,
            "breakdown": self.breakdown.to_dict(),
            "tie_breaker": self.tie_breaker,
            "ranked_at": self.ranked_at,
            "schema_version": self.schema_version,
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class RankingResult:
    profile: str
    ranked_count: int
    opportunities: List[RankedOpportunity]
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=utc_now)
    schema_version: str = OOS_RANKING_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile,
            "ranked_count": self.ranked_count,
            "opportunities": [item.to_dict() for item in self.opportunities],
            "telemetry": dict(self.telemetry),
            "generated_at": self.generated_at,
            "schema_version": self.schema_version,
            "read_only": self.read_only,
        }


class OpportunityRankingEngine:
    schema_version = OOS_RANKING_VERSION
    read_only = True

    def rank(
        self,
        opportunities: Iterable[Any],
        profile: RankingProfile | str = RankingProfile.BALANCED,
        limit: Optional[int] = None,
    ) -> RankingResult:
        profile = self._profile(profile)
        scored: List[RankedOpportunity] = []

        for opportunity in opportunities:
            self._validate_opportunity(opportunity)
            fingerprint = str(opportunity.fingerprint())
            breakdown = self.score(opportunity, profile)
            tie_breaker = self._tie_breaker(opportunity, fingerprint)

            scored.append(
                RankedOpportunity(
                    rank=0,
                    opportunity=opportunity,
                    fingerprint=fingerprint,
                    score=breakdown.normalized_score,
                    profile=profile.value,
                    breakdown=breakdown,
                    tie_breaker=tie_breaker,
                )
            )

        scored.sort(key=lambda item: (-item.score, item.tie_breaker))

        if limit is not None:
            scored = scored[: max(0, int(limit))]

        ranked = [
            RankedOpportunity(
                rank=index + 1,
                opportunity=item.opportunity,
                fingerprint=item.fingerprint,
                score=item.score,
                profile=item.profile,
                breakdown=item.breakdown,
                tie_breaker=item.tie_breaker,
                ranked_at=item.ranked_at,
            )
            for index, item in enumerate(scored)
        ]

        scores = [item.score for item in ranked]

        return RankingResult(
            profile=profile.value,
            ranked_count=len(ranked),
            opportunities=ranked,
            telemetry={
                "engine": "OpportunityRankingEngine",
                "profile": profile.value,
                "input_count": len(list(opportunities)) if isinstance(opportunities, list) else len(ranked),
                "ranked_count": len(ranked),
                "top_score": max(scores) if scores else 0.0,
                "average_score": round(sum(scores) / len(scores), 6) if scores else 0.0,
                "read_only": True,
                "generated_at": utc_now(),
            },
        )

    def rank_oos(
        self,
        oos: Any,
        profile: RankingProfile | str = RankingProfile.BALANCED,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> RankingResult:
        if active_only:
            records = oos.active_records()
        else:
            records = oos.all_records()

        opportunities = [record.opportunity for record in records]
        return self.rank(opportunities, profile=profile, limit=limit)

    def score(self, opportunity: Any, profile: RankingProfile | str = RankingProfile.BALANCED) -> RankingScoreBreakdown:
        profile = self._profile(profile)
        weights = PROFILE_WEIGHTS[profile]

        confidence_value = _clamp(getattr(opportunity, "confidence", 0.0))
        edge_value = _clamp(abs(float(getattr(opportunity, "expected_edge", 0.0))))
        liquidity_value = _clamp(getattr(opportunity, "liquidity_score", 0.5))

        time_window = getattr(opportunity, "time_window", None)
        freshness_value = _clamp(getattr(time_window, "freshness_score", 1.0))
        urgency_value = _clamp(getattr(time_window, "urgency_score", 0.0))

        risk_value = _clamp(getattr(opportunity, "risk_score", 0.5))

        execution = getattr(opportunity, "execution", None)
        execution_value = _clamp(getattr(execution, "execution_difficulty", 0.5))
        capital_value = self._capital_penalty(getattr(execution, "capital_required", None))

        confidence = confidence_value * weights["confidence"]
        edge = edge_value * weights["edge"]
        liquidity = liquidity_value * weights["liquidity"]
        freshness = freshness_value * weights["freshness"]
        urgency = urgency_value * weights["urgency"]
        risk_penalty = risk_value * abs(weights["risk"])
        execution_penalty = execution_value * abs(weights["execution"])
        capital_penalty = capital_value * abs(weights["capital"])

        raw = confidence + edge + liquidity + freshness + urgency - risk_penalty - execution_penalty - capital_penalty
        normalized = round(max(0.0, min(1.0, raw)), 6)

        return RankingScoreBreakdown(
            confidence=round(confidence, 6),
            edge=round(edge, 6),
            liquidity=round(liquidity, 6),
            freshness=round(freshness, 6),
            urgency=round(urgency, 6),
            risk_penalty=round(risk_penalty, 6),
            execution_penalty=round(execution_penalty, 6),
            capital_penalty=round(capital_penalty, 6),
            raw_score=round(raw, 6),
            normalized_score=normalized,
            profile=profile.value,
        )

    def _profile(self, profile: RankingProfile | str) -> RankingProfile:
        if isinstance(profile, RankingProfile):
            return profile
        try:
            return RankingProfile(str(profile))
        except Exception:
            return RankingProfile.BALANCED

    def _capital_penalty(self, capital_required: Any) -> float:
        if capital_required is None:
            return 0.0
        try:
            capital = float(capital_required)
            if capital <= 0:
                return 0.0
            if capital <= 100:
                return 0.10
            if capital <= 1000:
                return 0.30
            if capital <= 10000:
                return 0.60
            return 1.0
        except Exception:
            return 0.5

    def _tie_breaker(self, opportunity: Any, fingerprint: str) -> str:
        created_at = str(getattr(opportunity, "created_at", ""))
        opportunity_id = str(getattr(opportunity, "opportunity_id", ""))
        return f"{created_at}|{fingerprint}|{opportunity_id}"

    def _validate_opportunity(self, opportunity: Any) -> None:
        if opportunity is None:
            raise ValueError("Opportunity cannot be None.")

        if not bool(getattr(opportunity, "read_only", False)):
            raise ValueError("Opportunity must be read_only.")

        if not callable(getattr(opportunity, "fingerprint", None)):
            raise ValueError("Opportunity must expose fingerprint().")

        if not callable(getattr(opportunity, "to_dict", None)):
            raise ValueError("Opportunity must expose to_dict().")


def _clamp(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def build_ranking_engine() -> OpportunityRankingEngine:
    return OpportunityRankingEngine()


__all__ = [
    "OOS_RANKING_VERSION",
    "RankingProfile",
    "PROFILE_WEIGHTS",
    "RankingScoreBreakdown",
    "RankedOpportunity",
    "RankingResult",
    "OpportunityRankingEngine",
    "build_ranking_engine",
]
