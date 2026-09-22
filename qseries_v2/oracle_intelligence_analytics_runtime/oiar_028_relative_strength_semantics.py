
from __future__ import annotations
OIAR_028_BUILD_ID="OIAR-028"
OIAR_028_REVISION="OIAR_028_RELATIVE_STRENGTH_SEMANTICS_V1"
EXECUTION_AUTHORITY=False
def score_market(m):
    setup=str(m.get("setup_status") or "")
    live={"STRONG":30,"DEVELOPING":18,"WEAK":5}.get(str(m.get("live_evidence") or ""),0)
    hist={"STRONG":20,"MODERATE":12,"LIMITED":4}.get(str(m.get("historical_strength") or ""),0)
    direction=10 if str(m.get("direction") or "NEUTRAL")!="NEUTRAL" else 0
    setup_score={"WORTH_WATCHING_NOW":40,"SETUP_FORMING":20,"NO_CONFIRMED_EDGE":0}.get(setup,0)
    return setup_score+live+hist+direction
def rank_relative(markets):
    return tuple(sorted((dict(m) for m in markets),key=lambda m:(-score_market(m),str(m.get("market_id") or ""))))
def strongest_assessment(markets):
    ranked=rank_relative(markets)
    if not ranked:return {"market":None,"clears_edge":False,"message":"Oracle has no markets to rank in the current snapshot."}
    top=ranked[0];clears=str(top.get("setup_status") or "")=="WORTH_WATCHING_NOW"
    return {"market":top,"clears_edge":clears,"message":("This is Oracle's strongest current setup and it clears the edge threshold." if clears else "This is the strongest market in the current group, but it still does not clear Oracle's edge threshold.")}
