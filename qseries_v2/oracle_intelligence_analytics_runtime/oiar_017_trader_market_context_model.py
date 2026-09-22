from __future__ import annotations
from dataclasses import dataclass
from .oiar_016_canonical_market_identity_resolver import resolve_canonical_market_identity

OIAR_017_BUILD_ID="OIAR-017"
OIAR_017_REVISION="OIAR_017_TRADER_MARKET_CONTEXT_MODEL_V1"

@dataclass(frozen=True)
class TraderMarketContext:
    market_id:str
    display_name:str
    event_ticker:str|None
    historical_strength:str
    live_evidence:str
    direction:str
    setup_quality:str
    identity_status:str
    read_only:bool=True
    execution_authority:bool=False

def _historical(row):
    m=str(row.maturity or "").upper();r=float(row.reliability or 0)
    return "STRONG" if m=="PROVEN" and r>=.60 else "MODERATE" if m in ("PROVEN","MATURE") or r>=.50 else "LIMITED"

def _live(row):
    n=int(row.history_rows or 0);u=float(row.usefulness_score or 0)
    return "STRONG" if n>=20 and u>=50 else "DEVELOPING" if n>=8 or u>=25 else "WEAK"

def build_trader_market_context(root,row):
    ident=resolve_canonical_market_identity(root,row.market_id)
    title=ident.market_title if ident.resolved and ident.market_title else "Identity unresolved"
    admission=str(row.admission_status or "").lower()
    candidate=str(row.candidate_family or "none").lower()
    setup="ACTIONABLE_RESEARCH" if admission=="admitted" else "FORMING" if candidate!="none" else "NO_CONFIRMED_SETUP"
    return TraderMarketContext(
        row.market_id,title,ident.event_ticker,_historical(row),_live(row),
        str(row.research_direction or "neutral").upper(),setup,
        "RESOLVED" if ident.resolved else "UNRESOLVED",True,False
    )
