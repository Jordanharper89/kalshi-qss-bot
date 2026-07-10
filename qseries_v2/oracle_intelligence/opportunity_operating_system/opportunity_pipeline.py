"""
OOS-003 Opportunity Pipeline

Connects UniversalOpportunity intake, OOS registry, duplicate handling,
and opportunity ranking into one read-only Oracle opportunity flow.

Oracle discovers.
OOS manages and ranks.
Decision Layer selects later.
Q Series executes later.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


OOS_PIPELINE_VERSION = "OOS-003"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OpportunityPipelineItem:
    opportunity_id: str
    fingerprint: str
    intake_status: str
    duplicate: bool
    registered: bool
    source: str
    message: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityPipelineResult:
    status: str
    input_count: int
    registered_count: int
    duplicate_count: int
    ranked_count: int
    items: List[OpportunityPipelineItem]
    ranking_result: Any
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=utc_now)
    schema_version: str = OOS_PIPELINE_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        ranking_to_dict = getattr(self.ranking_result, "to_dict", None)
        ranking_data = ranking_to_dict() if callable(ranking_to_dict) else self.ranking_result

        return {
            "status": self.status,
            "input_count": self.input_count,
            "registered_count": self.registered_count,
            "duplicate_count": self.duplicate_count,
            "ranked_count": self.ranked_count,
            "items": [item.to_dict() for item in self.items],
            "ranking_result": ranking_data,
            "telemetry": dict(self.telemetry),
            "generated_at": self.generated_at,
            "schema_version": self.schema_version,
            "read_only": self.read_only,
        }


class OpportunityPipeline:
    schema_version = OOS_PIPELINE_VERSION
    read_only = True

    def __init__(self, oos: Optional[Any] = None, ranking_engine: Optional[Any] = None):
        if oos is None:
            from qseries_v2.oracle_intelligence.opportunity_operating_system import build_oos
            oos = build_oos()

        if ranking_engine is None:
            from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_ranking_engine import (
                build_ranking_engine,
            )
            ranking_engine = build_ranking_engine()

        self.oos = oos
        self.ranking_engine = ranking_engine

    def process(
        self,
        opportunities: Iterable[Any],
        source: str = "oracle",
        profile: str = "balanced",
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> OpportunityPipelineResult:
        opportunities = list(opportunities)
        items: List[OpportunityPipelineItem] = []

        for opportunity in opportunities:
            self._validate_opportunity(opportunity)

            intake = self.oos.intake(
                opportunity,
                source=source,
                metadata={
                    "pipeline": self.schema_version,
                    "processed_at": utc_now(),
                },
            )

            items.append(
                OpportunityPipelineItem(
                    opportunity_id=intake.opportunity_id,
                    fingerprint=intake.fingerprint,
                    intake_status=intake.status,
                    duplicate=bool(intake.duplicate),
                    registered=not bool(intake.duplicate),
                    source=source,
                    message=intake.message,
                )
            )

        ranking_result = self.ranking_engine.rank_oos(
            self.oos,
            profile=profile,
            active_only=active_only,
            limit=limit,
        )

        registered_count = sum(1 for item in items if item.registered)
        duplicate_count = sum(1 for item in items if item.duplicate)
        status = "ok"

        return OpportunityPipelineResult(
            status=status,
            input_count=len(opportunities),
            registered_count=registered_count,
            duplicate_count=duplicate_count,
            ranked_count=getattr(ranking_result, "ranked_count", 0),
            items=items,
            ranking_result=ranking_result,
            telemetry={
                "pipeline": self.schema_version,
                "source": source,
                "profile": profile,
                "active_only": active_only,
                "limit": limit,
                "input_count": len(opportunities),
                "registered_count": registered_count,
                "duplicate_count": duplicate_count,
                "ranked_count": getattr(ranking_result, "ranked_count", 0),
                "oos_total_registered": self.oos.telemetry().total_registered,
                "oos_active_count": self.oos.telemetry().active_count,
                "read_only": True,
                "generated_at": utc_now(),
            },
        )

    def ranked_feed(
        self,
        profile: str = "balanced",
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> Any:
        return self.ranking_engine.rank_oos(
            self.oos,
            profile=profile,
            active_only=active_only,
            limit=limit,
        )

    def telemetry(self) -> Dict[str, Any]:
        oos_telemetry = self.oos.telemetry().to_dict()

        return {
            "pipeline": self.schema_version,
            "read_only": True,
            "oos": oos_telemetry,
            "generated_at": utc_now(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "read_only": self.read_only,
            "telemetry": self.telemetry(),
            "oos": self.oos.to_dict(),
        }

    def _validate_opportunity(self, opportunity: Any) -> None:
        if opportunity is None:
            raise ValueError("Opportunity cannot be None.")

        if not bool(getattr(opportunity, "read_only", False)):
            raise ValueError("Opportunity must be read_only.")

        if not callable(getattr(opportunity, "fingerprint", None)):
            raise ValueError("Opportunity must expose fingerprint().")

        if not callable(getattr(opportunity, "to_dict", None)):
            raise ValueError("Opportunity must expose to_dict().")


def build_pipeline(oos: Optional[Any] = None, ranking_engine: Optional[Any] = None) -> OpportunityPipeline:
    return OpportunityPipeline(oos=oos, ranking_engine=ranking_engine)


__all__ = [
    "OOS_PIPELINE_VERSION",
    "OpportunityPipelineItem",
    "OpportunityPipelineResult",
    "OpportunityPipeline",
    "build_pipeline",
]
