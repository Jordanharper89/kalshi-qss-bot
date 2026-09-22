from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class CanonicalEventBinding:
    ticker:str
    league:str
    market_entities:Tuple[str,...]
    canonical_event_id:str|None
    canonical_home:str|None
    canonical_away:str|None
    status:str
    reasons:Tuple[str,...]
    execution_authority:bool=False

def bind_exact(ticker,league,market_entities,*,canonical_event_id=None,canonical_home=None,canonical_away=None,ambiguity=()):
    ents=tuple(str(x).strip() for x in market_entities if str(x).strip())
    amb=tuple(str(x) for x in ambiguity)
    if amb:
        return CanonicalEventBinding(str(ticker),str(league),ents,None,None,None,"AMBIGUOUS",amb,False)
    if not (ticker and league and ents and canonical_event_id and canonical_home and canonical_away):
        return CanonicalEventBinding(str(ticker),str(league),ents,None,None,None,"UNBOUND",("INSUFFICIENT_EXACT_IDENTITY",),False)
    normalized={x.casefold() for x in ents}
    teams={str(canonical_home).casefold(),str(canonical_away).casefold()}
    if not normalized.issubset(teams):
        return CanonicalEventBinding(str(ticker),str(league),ents,None,None,None,"REJECTED",("ENTITY_MISMATCH",),False)
    return CanonicalEventBinding(str(ticker),str(league),ents,str(canonical_event_id),str(canonical_home),str(canonical_away),"BOUND",(),False)
