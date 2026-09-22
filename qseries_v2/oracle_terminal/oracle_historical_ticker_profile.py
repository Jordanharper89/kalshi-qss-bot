from __future__ import annotations
from dataclasses import dataclass
from .oracle_historical_experience_read_model import HistoricalExperienceReadModel
OHE_003_BUILD_ID="OHE-003";OHE_003_REVISION="OHE_003_HISTORICAL_TICKER_PROFILE_V1"
@dataclass(frozen=True)
class HistoricalTickerProfile:
    ticker:str;family:str;exact_learned_records:int;family_learned_records:int;current_context_found:bool;maturity:str;experience_available:bool;regime_id:str;reliability:float;reason:str;learner_state_hash:str;lineage_current:bool;read_only:bool=True;execution_authority:bool=False
def build_historical_ticker_profile(model,ticker):
    if not isinstance(model,HistoricalExperienceReadModel):raise TypeError("model must be HistoricalExperienceReadModel")
    t=str(ticker or "").strip().upper()
    if not t:raise ValueError("ticker required")
    family=t.split("-",1)[0];exact=dict(model.learned_market_counts);families=dict(model.learned_family_counts);current=None
    for c in model.contexts:
        if c.market_ticker.upper()==t:current=c;break
    if current is None:
        for c in model.contexts:
            if c.market_ticker.upper().split("-",1)[0]==family:current=c;break
    return HistoricalTickerProfile(t,family,int(exact.get(t,0)),int(families.get(family,0)),current is not None,current.maturity if current else ("LEARNED_FAMILY" if families.get(family,0) else "BLIND"),bool(current.experience_available) if current else False,current.regime_id if current else "",float(current.reliability) if current else 0.0,current.reason if current else ("HISTORICAL_FAMILY_ONLY" if families.get(family,0) else "NO_LEARNED_HISTORY"),model.learner_state_hash,model.lineage_current,True,False)
