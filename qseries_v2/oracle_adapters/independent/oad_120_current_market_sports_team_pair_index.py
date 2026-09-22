from __future__ import annotations
from dataclasses import dataclass
import re

from .oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _norm(v):
    return " ".join(re.findall(r"[a-z0-9]+",str(v or "").lower()))

def _market_text(m):
    return _norm(" ".join(str(m.get(k,"") or "") for k in (
        "ticker","event_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary"
    )))

@dataclass(frozen=True, slots=True)
class SportsMarketCandidate:
    observation_id: str
    market_id: str
    away_team: str
    home_team: str
    matched_teams: tuple
    association_strength: str
    candidate_only: bool=True

def candidate_markets_for_sports_descriptor(descriptor, markets, max_candidates=25):
    away=_norm(descriptor.away_team)
    home=_norm(descriptor.home_team)
    if not away or not home:
        return ()
    out=[]
    for m in tuple(markets):
        ticker=str(m.get("ticker","")).strip()
        if not ticker: continue
        text=_market_text(m)
        hits=tuple(x for x in (away,home) if x and x in text)
        if len(hits)==2:
            out.append(SportsMarketCandidate(
                observation_id=descriptor.observation_id,
                market_id=ticker,
                away_team=descriptor.away_team,
                home_team=descriptor.home_team,
                matched_teams=hits,
                association_strength="EXACT_TWO_TEAM_PAIR",
                candidate_only=True,
            ))
    return tuple(sorted(out,key=lambda x:x.market_id)[:max_candidates])

def fetch_current_market_sports_candidates(descriptors, limit=1000, timeout_seconds=20):
    markets,_=fetch_current_open_kalshi_market_index(limit=limit,timeout_seconds=timeout_seconds)
    groups=tuple((d,candidate_markets_for_sports_descriptor(d,markets)) for d in tuple(descriptors))
    return tuple(markets),groups
