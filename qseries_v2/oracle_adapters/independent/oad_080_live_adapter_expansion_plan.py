from __future__ import annotations
from dataclasses import dataclass

from qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import rank_live_source_coverage_gaps

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True,slots=True)
class AdapterBuildRecommendation:
    rank:int
    topic:str
    source_family:str
    live_markets:int
    reason:str

@dataclass(frozen=True,slots=True)
class AdapterExpansionPlan:
    evaluated_markets:int
    recommendations:tuple[AdapterBuildRecommendation,...]
    held_topics:tuple[str,...]

def build_live_adapter_expansion_plan(limit=1000,max_recommendations=10):
    gaps=rank_live_source_coverage_gaps(limit)
    recs=[]
    held=[]
    rank=1
    total=sum(x.live_markets for x in gaps)
    for gap in gaps:
        if gap.topic=="other":
            held.append(gap.topic)
            continue
        if not gap.missing_source_families:
            continue
        for family in gap.missing_source_families:
            recs.append(AdapterBuildRecommendation(
                rank,gap.topic,family,gap.live_markets,
                "live_market_demand_requires_independent_authoritative_coverage"
            ))
            rank+=1
            if len(recs)>=int(max_recommendations):
                break
        if len(recs)>=int(max_recommendations):
            break
    return AdapterExpansionPlan(total,tuple(recs),tuple(sorted(set(held))))
