\

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .oad_271_solana_historical_experience_formation import build_solana_historical_experiences

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaOutcomePendingCase:
    experience_id:str; token_address:str; pair_address:str; snapshot_at:str
    conditions:tuple; evidence_observation_ids:tuple; horizon_seconds:int
    state:str="OUTCOME_PENDING"; execution_authority:bool=False

def build_outcome_pending_solana_cases(records,horizons=(15,30,60)):
    out=[]
    for x in build_solana_historical_experiences(records):
        for h in tuple(int(v) for v in horizons if int(v)>0):
            out.append(SolanaOutcomePendingCase(
                x.experience_id,x.token_address,x.pair_address,x.snapshot_at,
                x.conditions,x.evidence_observation_ids,h,"OUTCOME_PENDING",False
            ))
    return tuple(out)

