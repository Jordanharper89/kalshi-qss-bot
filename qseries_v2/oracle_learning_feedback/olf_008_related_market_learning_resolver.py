from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .olf_006_structural_identity import resolve_structural_identity
from .olf_007_cross_market_learning_index import load_cross_market_learning_index

OLF_008_BUILD_ID="OLF-008"
OLF_008_REVISION="OLF_008_RELATED_MARKET_LEARNING_RESOLVER_V1"

@dataclass(frozen=True)
class RelatedMarketLearningResolution:
    market_ticker:str
    relationship_type:str
    relationship_strength:float
    source_markets:tuple
    learned_records:int
    generalized_experience_weight:float
    learner_state_hash:str
    available:bool
    directional_signal_available:bool=False
    execution_authority:bool=False

def resolve_related_market_learning(root=None,market_ticker=""):
    root=Path(root or Path.cwd()).resolve()
    ident=resolve_structural_identity(market_ticker)
    idx=load_cross_market_learning_index(root)
    state_hash=str(idx.get("learner_state_hash") or "")
    exact=idx.get("exact",{}).get(ident.exact_key)
    if exact:
        records=int(exact.get("learned_records",0))
        return RelatedMarketLearningResolution(
            ident.market_ticker,"EXACT_TICKER",1.0,(ident.market_ticker,),records,
            min(1.0,records/25.0),state_hash,records>0,False,False
        )

    rows=tuple(idx.get("series",{}).get(ident.series_key,()))
    if not rows:
        return RelatedMarketLearningResolution(
            ident.market_ticker,"NONE",0.0,tuple(),0,0.0,state_hash,False,False,False
        )

    source=tuple(sorted(str(x.get("market_ticker") or "") for x in rows if x.get("market_ticker")))
    records=sum(int(x.get("learned_records",0)) for x in rows)
    # Same exact venue series is strong historical analogy, but never treated as identical.
    strength=.75
    weight=min(1.0,records/25.0)*strength
    return RelatedMarketLearningResolution(
        ident.market_ticker,"SAME_KALSHI_SERIES",strength,source,records,weight,
        state_hash,records>0,False,False
    )

def verify_olf_008_related_market_learning_resolver():
    return OLF_008_BUILD_ID=="OLF-008" and callable(resolve_related_market_learning)
