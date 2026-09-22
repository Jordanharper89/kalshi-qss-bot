import re
from dataclasses import dataclass,asdict
from qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver import resolve_sports_market_type

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

SUPPORTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")

@dataclass(frozen=True)
class ExactSportsPropositionContext:
    parent_ticker:str
    market_ticker:str
    event_ticker:str
    side:str
    league:str|None
    proposition_type:str
    title:str
    subtitle:str
    yes_sub_title:str
    no_sub_title:str
    status:str
    reasons:tuple
    execution_authority:bool=False

def infer_league(ticker,event_ticker,title=""):
    text=" ".join((str(ticker),str(event_ticker),str(title))).upper()
    rules=(
        ("NCAAF",("KXNCAAF","NCAAF")),
        ("NFL",("KXNFL"," NFL ")),
        ("NBA",("KXNBA"," NBA ")),
        ("NHL",("KXNHL"," NHL ")),
        ("EPL",("KXEPL","PREMIER LEAGUE")),
        ("MLS",("KXMLS"," MLS ")),
    )
    hits=[league for league,terms in rules if any(term in f" {text} " for term in terms)]
    return hits[0] if len(set(hits))==1 else None

def reconstruct(row):
    market=dict(row.get("market") or {})
    ticker=str(row.get("market_ticker") or market.get("ticker") or "").strip().upper()
    event=str(row.get("event_ticker") or market.get("event_ticker") or "").strip().upper()
    title=str(market.get("title") or market.get("market_title") or "").strip()
    subtitle=str(market.get("subtitle") or "").strip()
    yes=str(market.get("yes_sub_title") or "").strip()
    no=str(market.get("no_sub_title") or "").strip()
    league=infer_league(ticker,event,title)
    mt=resolve_sports_market_type(market)
    ptype=str(getattr(mt,"market_type","sports_other"))
    reasons=[]
    if row.get("status")!="RESOLVED": reasons.append("EXACT_MARKET_NOT_RESOLVED")
    if not league: reasons.append("SUPPORTED_LEAGUE_NOT_RESOLVED")
    if ptype in ("non_sports","sports_other"): reasons.append("PROPOSITION_TYPE_NOT_EXACT")
    status="READY" if not reasons else "HELD"
    return ExactSportsPropositionContext(
        str(row.get("parent_ticker") or ""),ticker,event,str(row.get("side") or ""),
        league,ptype,title,subtitle,yes,no,status,tuple(reasons),False)

def reconstruct_rows(rows):
    return tuple(reconstruct(r) for r in rows)
