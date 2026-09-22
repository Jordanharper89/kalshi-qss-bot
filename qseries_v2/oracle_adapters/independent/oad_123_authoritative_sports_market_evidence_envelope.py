from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class AuthoritativeSportsMarketEvidence:
    observation_id: str
    market_id: str
    source_id: str
    sport_family: str
    subject: str
    away_team: str
    home_team: str
    evidence_type: str
    association_strength: str
    independent_evidence: bool
    candidate_only: bool
    direction: None=None
    probability: None=None
    execution_authority: bool=False

def build_sports_market_evidence_envelopes(report):
    descriptors={d.observation_id:d for d in tuple(report.descriptors)}
    out=[]
    for a in tuple(report.associations):
        d=descriptors.get(a.observation_id)
        if d is None:
            raise RuntimeError("association references unknown sports observation")
        if d.independent_evidence is not True:
            raise RuntimeError("sports evidence is not independent")
        if a.candidate_only is not True:
            raise RuntimeError("sports market association must remain candidate-only")
        out.append(AuthoritativeSportsMarketEvidence(
            observation_id=d.observation_id,
            market_id=a.market_id,
            source_id=d.source_id,
            sport_family=d.sport_family,
            subject=d.subject,
            away_team=d.away_team,
            home_team=d.home_team,
            evidence_type=d.evidence_type,
            association_strength=a.association_strength,
            independent_evidence=True,
            candidate_only=True,
            direction=None,
            probability=None,
            execution_authority=False,
        ))
    return tuple(out)
