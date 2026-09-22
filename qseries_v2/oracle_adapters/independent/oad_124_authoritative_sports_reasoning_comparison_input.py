from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class SportsReasoningComparisonInput:
    market_id: str
    evidence: tuple
    independent_source_ids: tuple
    evidence_count: int
    independent_evidence_count: int
    candidate_only: bool
    direction: None=None
    probability: None=None
    execution_authority: bool=False

def build_sports_reasoning_comparison_inputs(envelopes):
    groups=defaultdict(list)
    for e in tuple(envelopes):
        if e.independent_evidence is not True or e.candidate_only is not True:
            raise RuntimeError("only independent candidate-only sports evidence may enter reasoning comparison")
        if e.direction is not None or e.probability is not None:
            raise RuntimeError("direction/probability must not be manufactured by adapter layer")
        groups[e.market_id].append(e)
    out=[]
    for market_id in sorted(groups):
        evidence=tuple(groups[market_id])
        sources=tuple(sorted({e.source_id for e in evidence}))
        out.append(SportsReasoningComparisonInput(
            market_id=market_id,
            evidence=evidence,
            independent_source_ids=sources,
            evidence_count=len(evidence),
            independent_evidence_count=len(evidence),
            candidate_only=True,
            direction=None,
            probability=None,
            execution_authority=False,
        ))
    return tuple(out)
