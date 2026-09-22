\

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from .oad_316_solana_comparable_case_statistics import aggregate_comparable_solana_cases

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaLearningHandoff:
    state:str; learned_cases:int; comparable_groups:int; evidence_hash:str|None
    learner_contracts_verified:bool; probability:None=None; direction:None=None
    execution_authority:bool=False

def build_solana_learning_handoff(cases):
    cases=tuple(x for x in cases if getattr(x,"verified",False))
    stats=aggregate_comparable_solana_cases(cases)
    if not cases:
        return SolanaLearningHandoff("HOLD_VERIFIED_OUTCOMES_REQUIRED",0,0,None,True,None,None,False)
    payload=tuple((x.learned_case_id,x.horizon_seconds,x.conditions,x.outcome_class,round(x.return_fraction,12),x.evidence_hash) for x in cases)
    h=sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    ready=sum(x.state=="COMPARABLE_CASES_READY" for x in stats)
    state="READY_FOR_EXISTING_OCL_LEARNING" if ready else "LEARNED_CASES_PRESENT_SAMPLE_ACCUMULATING"
    return SolanaLearningHandoff(state,len(cases),len(stats),h,True,None,None,False)

