from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .olf_006_structural_identity import resolve_structural_identity
from .olf_024_regime_aware_experience import select_regime_aware_experience
from .olf_028_series_maturity import materialize_series_maturity

OLF_029_BUILD_ID="OLF-029";OLF_029_REVISION="OLF_029_BREADTH_AWARE_EXPERIENCE_SELECTOR_V1"

@dataclass(frozen=True)
class BreadthAwareExperience:
    market_ticker:str;series_key:str;maturity:str;series_admitted:bool;experience_available:bool;regime_id:str;reliability:float;learner_state_hash:str;reason:str;execution_authority:bool=False

def select_breadth_aware_experience(root=None,market_ticker="",source_rows=()):
    root=Path(root or Path.cwd()).resolve();ident=resolve_structural_identity(market_ticker);m=materialize_series_maturity(root)
    by={str(x["series_key"]):x for x in m["series"]};row=by.get(ident.series_key)
    if row is None:
        return BreadthAwareExperience(ident.market_ticker,ident.series_key,"BLIND",False,False,"",0.0,m["learner_state_hash"],"NO_LEARNED_SERIES_HISTORY",False)
    if not row["reasoning_admitted"]:
        return BreadthAwareExperience(ident.market_ticker,ident.series_key,row["maturity"],False,False,"",0.0,m["learner_state_hash"],"SERIES_HISTORY_NOT_MATURE_ENOUGH",False)
    x=select_regime_aware_experience(root,ident.market_ticker,source_rows)
    if not x.available:
        return BreadthAwareExperience(ident.market_ticker,ident.series_key,row["maturity"],True,False,x.regime_id,x.recency_reliability,m["learner_state_hash"],x.reason,False)
    return BreadthAwareExperience(ident.market_ticker,ident.series_key,row["maturity"],True,True,x.regime_id,x.recency_reliability,m["learner_state_hash"],"MATURE_SERIES_AND_MATCHED_REGIME",False)

def verify_olf_029_breadth_aware_experience_selector():
    return OLF_029_BUILD_ID=="OLF-029" and callable(select_breadth_aware_experience)
