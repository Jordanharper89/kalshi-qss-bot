\

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from .oad_314_solana_verified_forward_outcome_attribution import SolanaVerifiedForwardOutcome

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaLearnedCase:
    learned_case_id:str; experience_id:str; token_address:str; pair_address:str
    horizon_seconds:int; conditions:tuple; outcome_class:str; return_fraction:float
    evidence_observation_ids:tuple; evidence_hash:str; verified:bool=True
    execution_authority:bool=False

def _hash(v): return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def build_verified_solana_learned_cases(pending_cases,outcomes):
    pending={(x.experience_id,x.horizon_seconds):x for x in pending_cases}
    out=[]
    for o in outcomes:
        c=pending.get((o.experience_id,o.horizon_seconds))
        if c is None or not o.verified: continue
        ev=tuple(dict.fromkeys(tuple(c.evidence_observation_ids)+tuple(o.evidence_observation_ids)))
        eh=_hash(ev)
        lid="solana-learned:"+_hash((o.experience_id,o.horizon_seconds,c.conditions,o.outcome_class,round(o.return_fraction,12),eh))[:32]
        out.append(SolanaLearnedCase(lid,o.experience_id,o.token_address,o.pair_address,o.horizon_seconds,c.conditions,o.outcome_class,o.return_fraction,ev,eh,True,False))
    return tuple(out)

