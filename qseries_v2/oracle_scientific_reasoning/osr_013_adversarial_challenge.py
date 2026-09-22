from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_013_BUILD_ID="OSR-013"
OSR_013_REVISION="OSR_013_ADVERSARIAL_HYPOTHESIS_CHALLENGE_ENGINE_V1"

@dataclass(frozen=True)
class HypothesisChallenge:
    challenge_id:str
    assumption:str
    severity:float
    falsification_power:float
    evidence_gap:float

@dataclass(frozen=True)
class AdversarialChallengeResult:
    hypothesis_id:str
    challenges:tuple[HypothesisChallenge,...]
    vulnerability_score:float
    strongest_challenge_id:str
    status:str

def challenge_hypothesis(hypothesis_id,challenges):
    rows=tuple(challenges)
    if not hypothesis_id or not rows: raise ValueError("hypothesis and challenges required")
    seen=set()
    scored=[]
    for c in rows:
        if c.challenge_id in seen: raise ValueError("duplicate challenge")
        seen.add(c.challenge_id)
        if not 0<=c.severity<=1 or not 0<=c.falsification_power<=1 or not 0<=c.evidence_gap<=1:
            raise ValueError("normalized challenge values required")
        score=c.severity*c.falsification_power*(.5+.5*c.evidence_gap)
        scored.append((score,c))
    scored=sorted(scored,key=lambda x:(-x[0],x[1].challenge_id))
    vulnerability=sum(x[0] for x in scored)/len(scored)
    status="high_risk" if vulnerability>=.6 else ("challenged" if vulnerability>=.3 else "resilient")
    return AdversarialChallengeResult(hypothesis_id,tuple(x[1] for x in scored),vulnerability,scored[0][1].challenge_id,status)

def build_osr_013_certification_manifest():
    return MappingProxyType({"build_id":OSR_013_BUILD_ID,"revision":OSR_013_REVISION,"purpose":"attack_leading_hypothesis","self_confirmation_bias_reduction":True,"execution":False})

def verify_osr_013_adversarial_hypothesis_challenge_engine():
    rows=(HypothesisChallenge("c1","timing",1,1,1),HypothesisChallenge("c2","source",.2,.2,.2))
    return challenge_hypothesis("h",rows).strongest_challenge_id=="c1"
