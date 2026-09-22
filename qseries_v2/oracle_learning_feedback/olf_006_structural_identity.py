from __future__ import annotations
from dataclasses import dataclass
import re

OLF_006_BUILD_ID="OLF-006"
OLF_006_REVISION="OLF_006_LEARNED_MARKET_STRUCTURAL_IDENTITY_V1"

_TICKER=re.compile(r"^[A-Z0-9._:-]+(?:-[A-Z0-9._:-]+)*$")

@dataclass(frozen=True)
class LearnedMarketStructuralIdentity:
    market_ticker:str
    series_key:str
    series_token:str
    structural_depth:int
    exact_key:str
    execution_authority:bool=False

def normalize_ticker(value):
    ticker=str(value or "").strip().upper()
    if not ticker or not _TICKER.fullmatch(ticker):
        raise ValueError("invalid Kalshi market ticker")
    return ticker

def resolve_structural_identity(market_ticker):
    ticker=normalize_ticker(market_ticker)
    parts=tuple(x for x in ticker.split("-") if x)
    series=parts[0]
    # Strict production generalization boundary:
    # only the exact Kalshi series token is reusable across different contracts.
    return LearnedMarketStructuralIdentity(
        ticker,
        "kalshi:series:"+series,
        series,
        len(parts),
        "kalshi:ticker:"+ticker,
        False,
    )

def same_series(left,right):
    return resolve_structural_identity(left).series_key==resolve_structural_identity(right).series_key

def verify_olf_006_learned_market_structural_identity():
    a=resolve_structural_identity("KXBTC15M-26AUG192200-00")
    b=resolve_structural_identity("KXBTC15M-26AUG192215-15")
    c=resolve_structural_identity("KXETH15M-26AUG192200-00")
    return a.series_key==b.series_key and a.series_key!=c.series_key and not a.execution_authority
