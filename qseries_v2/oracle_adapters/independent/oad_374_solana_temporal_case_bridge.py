\

from __future__ import annotations
from dataclasses import dataclass
from .oad_373_solana_universal_economic_event_promotion import SolanaPromotedEconomicEvent

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaTemporalLearningCase:
    case_id:str
    anchor_slot:int
    anchor_time:float|None
    primary_asset:str|None
    secondary_asset:str|None
    protocol:str|None
    behavior_type:str
    horizons_seconds:tuple
    outcome_state:str
    source_event_id:str
    execution_authority:bool=False

def build_temporal_learning_case(event:SolanaPromotedEconomicEvent,horizons=(15,30,60)):
    if not event.promotable:
        raise ValueError("economic event is not promotable")
    hs=tuple(sorted({int(x) for x in horizons if int(x)>0}))
    if not hs:
        raise ValueError("at least one positive horizon required")
    return SolanaTemporalLearningCase(
        case_id="SOLANA:"+event.event_id,
        anchor_slot=int(event.slot),
        anchor_time=event.block_time,
        primary_asset=event.primary_asset,
        secondary_asset=event.secondary_asset,
        protocol=event.protocol,
        behavior_type=event.behavior_type,
        horizons_seconds=hs,
        outcome_state="OUTCOME_PENDING",
        source_event_id=event.event_id,
        execution_authority=False,
    )

