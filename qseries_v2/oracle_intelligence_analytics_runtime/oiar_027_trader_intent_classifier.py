
from __future__ import annotations
from dataclasses import dataclass
import re
OIAR_027_BUILD_ID="OIAR-027"
OIAR_027_REVISION="OIAR_027_TRADER_INTENT_CLASSIFIER_V1"
EXECUTION_AUTHORITY=False
@dataclass(frozen=True)
class TraderIntent:
    route:str
    ranking:str
    timeframe:str
    direction:str
    follow_up:bool
    confidence:float
TOKENS=("play","plays","like","strongest","best","watch","watching","setting up","setup","edge","market right now","anything good","anything worth","what are you seeing","what do you see","bullish","bearish","changed","that one","why")
def classify_trader_intent(query):
    q=" ".join(str(query or "").lower().split())
    trader=any(t in q for t in TOKENS)
    ranking="strongest" if any(t in q for t in ("strongest","best one","best setup","top play")) else "standard"
    timeframe="evening" if any(t in q for t in ("evening","tonight")) else "today" if "today" in q else "now" if any(t in q for t in ("right now","now","currently")) else "session"
    direction="bullish" if any(t in q for t in ("bullish","bull","upside")) else "bearish" if any(t in q for t in ("bearish","bear","downside")) else "any"
    follow=any(t in q for t in ("that one","why","changed","strongest")) and len(q.split())<=8
    return TraderIntent("trader_brief" if trader else "fallback",ranking,timeframe,direction,follow,0.95 if trader else 0.0)
