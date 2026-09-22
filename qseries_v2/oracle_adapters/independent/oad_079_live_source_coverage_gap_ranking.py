from __future__ import annotations
from dataclasses import dataclass

from qseries_v2.oracle_adapters.independent.oad_077_live_market_topic_inventory import build_live_topic_inventory
from qseries_v2.oracle_adapters.independent.oad_078_authoritative_source_requirement_map import requirements_for_topic

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

COVERED="COVERED"
NOT_COVERED="NOT_COVERED"
UNMAPPED="UNMAPPED"

@dataclass(frozen=True,slots=True)
class CoverageGap:
    topic:str
    live_markets:int
    required_source_families:tuple[str,...]
    missing_source_families:tuple[str,...]
    coverage_state:str
    priority_score:int

    @property
    def covered(self):
        return self.coverage_state==COVERED

def coverage_state(topic, requirements, missing_families):
    if str(topic)=="other" or not requirements:
        return UNMAPPED
    if missing_families:
        return NOT_COVERED
    return COVERED

def rank_live_source_coverage_gaps(limit=1000):
    inv=build_live_topic_inventory(limit)
    out=[]
    for topic,count in inv.topic_counts:
        req=requirements_for_topic(topic)
        required=tuple(x.source_family for x in req if x.source_family!="Unmapped")
        missing=tuple(
            x.source_family for x in req
            if not x.existing_adapter and x.source_family!="Unmapped"
        )
        state=coverage_state(topic,req,missing)
        urgency=3 if state==UNMAPPED else (2 if state==NOT_COVERED else 1)
        score=int(count)*1000 + urgency*100 + len(missing)
        out.append(
            CoverageGap(
                topic,
                int(count),
                required,
                missing,
                state,
                score,
            )
        )
    return tuple(sorted(out,key=lambda x:(-x.priority_score,x.topic)))
