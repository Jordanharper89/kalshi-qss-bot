from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
ORACLE = BASE / "oracle_intelligence"
OOS = ORACLE / "opportunity_operating_system"

MODULE_PATH = OOS / "opportunity_pipeline.py"
INIT_PATH = OOS / "__init__.py"
TEST_PATH = ROOT / "test_oos_003_opportunity_pipeline.py"

MODULE_CODE = r'''"""
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
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.opportunity_operating_system import build_oos
from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_pipeline import (
    OOS_PIPELINE_VERSION,
    OpportunityPipeline,
    build_pipeline,
)
from qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_ranking_engine import (
    build_ranking_engine,
)
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    OpportunityExecutionProfile,
    OpportunityTimeWindow,
    UniversalOpportunityFactory,
)


def _prediction_market(market_id="KXBTC-YES"):
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id=market_id,
        title=f"Prediction market {market_id}",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _scalp(market_id="KXBTC-YES", edge=0.12, confidence=0.84, liquidity=0.76, risk=0.31):
    market = _prediction_market(market_id)
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=market,
        fair_value=0.55 + edge,
        market_price=0.55,
        confidence=confidence,
        explanation=f"Oracle fair value gap for {market_id}.",
        liquidity_score=liquidity,
        risk_score=risk,
        time_window=OpportunityTimeWindow(urgency_score=0.50, freshness_score=1.0),
        execution=OpportunityExecutionProfile(
            required_execution_adapter="prediction_market",
            execution_difficulty=0.25,
            capital_required=100,
        ),
    )


def _settlement(market_id="KXSETTLE-YES"):
    market = _prediction_market(market_id)
    return UniversalOpportunityFactory.settlement_edge(
        market=market,
        payout_certainty=0.99,
        market_price=0.93,
        confidence=0.96,
        explanation="Settlement certainty exceeds market price.",
        liquidity_score=0.70,
        risk_score=0.15,
    )


def _arb():
    market = UniversalMarketFactory.from_arbitrage_pair(
        market_id="arb:btc:a:b",
        title="BTC cross-venue spread",
        venue_a="VenueA",
        venue_b="VenueB",
        asset="BTC",
        spread=0.018,
        liquidity=50000,
    )
    return UniversalOpportunityFactory.arbitrage_spread(
        market=market,
        spread=0.018,
        confidence=0.91,
        explanation="Cross-venue spread exceeds execution cost estimate.",
        liquidity_score=0.80,
        risk_score=0.20,
    )


def test_oos_003_processes_and_ranks_opportunities():
    pipeline = build_pipeline()
    opportunities = [
        _scalp("LOW", edge=0.04, confidence=0.60, liquidity=0.30, risk=0.60),
        _scalp("HIGH", edge=0.20, confidence=0.90, liquidity=0.80, risk=0.20),
        _scalp("MID", edge=0.10, confidence=0.75, liquidity=0.60, risk=0.35),
    ]

    result = pipeline.process(opportunities, source="test_engine")

    assert result.schema_version == OOS_PIPELINE_VERSION
    assert result.read_only is True
    assert result.status == "ok"
    assert result.input_count == 3
    assert result.registered_count == 3
    assert result.duplicate_count == 0
    assert result.ranked_count == 3
    assert result.ranking_result.opportunities[0].opportunity.market_id == "HIGH"


def test_oos_003_duplicate_handling():
    pipeline = build_pipeline()
    opportunity = _scalp("DUPLICATE", edge=0.12)

    first = pipeline.process([opportunity], source="engine_a")
    second = pipeline.process([opportunity], source="engine_b")

    assert first.registered_count == 1
    assert second.registered_count == 0
    assert second.duplicate_count == 1
    assert len(pipeline.oos.all_records()) == 1
    assert pipeline.oos.telemetry().duplicate_count == 1


def test_oos_003_ranked_feed_limit():
    pipeline = build_pipeline()
    pipeline.process(
        [
            _scalp("A", edge=0.05),
            _scalp("B", edge=0.20),
            _scalp("C", edge=0.10),
        ]
    )

    feed = pipeline.ranked_feed(limit=2)

    assert feed.ranked_count == 2
    assert feed.opportunities[0].rank == 1
    assert feed.opportunities[1].rank == 2


def test_oos_003_works_with_external_oos_and_ranking_engine():
    oos = build_oos()
    ranking_engine = build_ranking_engine()
    pipeline = OpportunityPipeline(oos=oos, ranking_engine=ranking_engine)

    result = pipeline.process([_settlement(), _arb()], source="multi_source")

    assert result.registered_count == 2
    assert len(oos.all_records()) == 2
    assert result.ranked_count == 2
    assert result.telemetry["oos_total_registered"] == 2


def test_oos_003_serialization_and_telemetry():
    pipeline = build_pipeline()
    pipeline.process([_scalp("SERIAL", edge=0.13)], source="serializer")

    data = pipeline.to_dict()
    telemetry = pipeline.telemetry()

    assert data["schema_version"] == OOS_PIPELINE_VERSION
    assert data["read_only"] is True
    assert telemetry["read_only"] is True
    assert telemetry["oos"]["total_registered"] == 1
    assert len(data["oos"]["records"]) == 1


def test_oos_003_rejects_non_read_only_objects():
    class BadOpportunity:
        read_only = False

        def fingerprint(self):
            return "bad"

        def to_dict(self):
            return {}

    pipeline = build_pipeline()

    try:
        pipeline.process([BadOpportunity()])
        raise AssertionError("Pipeline should reject non-read-only opportunity.")
    except ValueError:
        pass


def test_oos_003_profile_pass_through():
    pipeline = build_pipeline()

    high_edge = _scalp("HIGH_EDGE", edge=0.30, confidence=0.70, liquidity=0.50, risk=0.90)
    low_risk = _scalp("LOW_RISK", edge=0.08, confidence=0.88, liquidity=0.80, risk=0.05)

    ev_result = pipeline.process(
        [high_edge, low_risk],
        profile="max_expected_value",
    )

    risk_result = pipeline.ranked_feed(profile="lowest_risk")

    assert ev_result.ranking_result.profile == "max_expected_value"
    assert risk_result.profile == "lowest_risk"


if __name__ == "__main__":
    test_oos_003_processes_and_ranks_opportunities()
    test_oos_003_duplicate_handling()
    test_oos_003_ranked_feed_limit()
    test_oos_003_works_with_external_oos_and_ranking_engine()
    test_oos_003_serialization_and_telemetry()
    test_oos_003_rejects_non_read_only_objects()
    test_oos_003_profile_pass_through()

    pipeline = build_pipeline()
    result = pipeline.process(
        [
            _scalp("LOW", edge=0.04, confidence=0.60, liquidity=0.30, risk=0.60),
            _scalp("HIGH", edge=0.20, confidence=0.90, liquidity=0.80, risk=0.20),
            _scalp("MID", edge=0.10, confidence=0.75, liquidity=0.60, risk=0.35),
        ],
        source="test_engine",
    )

    print("[PASS] OOS-003 Opportunity Pipeline")
    print(
        {
            "schema_version": result.schema_version,
            "input_count": result.input_count,
            "registered_count": result.registered_count,
            "duplicate_count": result.duplicate_count,
            "ranked_count": result.ranked_count,
            "top_market": result.ranking_result.opportunities[0].opportunity.market_id,
            "read_only": result.read_only,
        }
    )
'''

def ensure_dirs():
    OOS.mkdir(parents=True, exist_ok=True)


def update_init():
    INIT_PATH.touch(exist_ok=True)
    text = INIT_PATH.read_text(encoding="utf-8")

    import_block = '''from .opportunity_pipeline import (
    OOS_PIPELINE_VERSION,
    OpportunityPipelineItem,
    OpportunityPipelineResult,
    OpportunityPipeline,
    build_pipeline,
)
'''

    if "from .opportunity_pipeline import" not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += import_block

    if "__all__" not in text:
        text += "\n__all__ = []\n"

    for item in [
        '"OOS_PIPELINE_VERSION"',
        '"OpportunityPipelineItem"',
        '"OpportunityPipelineResult"',
        '"OpportunityPipeline"',
        '"build_pipeline"',
    ]:
        if item not in text:
            text = text.replace("__all__ = [", f"__all__ = [\n    {item},")

    INIT_PATH.write_text(text, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OOS-003 INSTALLER")
    print(" Opportunity Pipeline")
    print("=" * 40)

    ensure_dirs()

    MODULE_PATH.write_text(MODULE_CODE, encoding="utf-8")
    print(f"[OK] Wrote {MODULE_PATH}")

    TEST_PATH.write_text(TEST_CODE, encoding="utf-8")
    print(f"[OK] Wrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print("\n[DONE] OOS-003 installed")
    print("\nRun:")
    print("py test_oos_002_opportunity_ranking_engine.py")
    print("py test_oos_003_opportunity_pipeline.py")


if __name__ == "__main__":
    main()