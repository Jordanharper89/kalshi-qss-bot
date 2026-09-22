
from __future__ import annotations
from dataclasses import dataclass
OIAR_029_BUILD_ID="OIAR-029"
OIAR_029_REVISION="OIAR_029_TRADER_SESSION_CONTEXT_V1"
EXECUTION_AUTHORITY=False
@dataclass
class TraderSessionContext:
 timeframe:str="now"
 direction:str="any"
 last_market_id:str=""
 last_market_title:str=""
 last_intent:str=""
def apply_intent(context,intent):
    if intent.timeframe!="session":context.timeframe=intent.timeframe
    if intent.direction!="any":context.direction=intent.direction
    context.last_intent=intent.ranking
    return context
def remember_market(context,market):
    if market:
        context.last_market_id=str(market.get("market_id") or "")
        context.last_market_title=str(market.get("market_title") or "")
    return context
