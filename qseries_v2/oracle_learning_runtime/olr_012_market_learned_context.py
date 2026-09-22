from __future__ import annotations
from dataclasses import dataclass
from .olr_011_learned_state_read_projection import LearnedStateProjection

@dataclass(frozen=True)
class MarketLearnedContext:
    market_ticker: str
    evidence_weight: float
    learned_confidence: float
    sample_size: int

def build_market_learned_context(p: LearnedStateProjection) -> MarketLearnedContext:
    weight=min(1.0,p.events_seen/100.0)
    confidence=(p.reliability*weight)+(0.5*(1.0-weight))
    return MarketLearnedContext(p.market_ticker,weight,confidence,p.events_seen)

def verify_olr_012_market_learned_context():
    p=LearnedStateProjection("KX",20,12,8,0.6,0.9)
    x=build_market_learned_context(p)
    return x.market_ticker=="KX" and 0.0 <= x.evidence_weight <= 1.0
