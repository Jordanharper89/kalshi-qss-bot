from __future__ import annotations
OIAR_033_BUILD_ID="OIAR-033"
OIAR_033_REVISION="OIAR_033_EVENT_SPORT_CONTEXT_V1"
EXECUTION_AUTHORITY=False
SPORT_RULES=(
 ("SOCCER",("both teams to score","goals scored","real madrid","atletico","valencia","draw")),
 ("BASEBALL",("runs scored","first 5 innings","philadelphia","cleveland","boston","milwaukee","pittsburgh","houston","chicago c","los angeles d")),
 ("TENNIS",("auger-aliassime","nakashima","musetti","gauff","sabalenka","svitolina","kostyuk","jovic")),
)
def classify_event_context(market):
    title=str(market.get("market_title") or market.get("title") or "").lower()
    explicit=str(market.get("sport") or market.get("category") or "").strip()
    if explicit:return {"sport":explicit.upper(),"event_context":explicit,"context_source":"SNAPSHOT"}
    scores=[]
    for sport,tokens in SPORT_RULES:
        n=sum(1 for token in tokens if token in title)
        if n:scores.append((n,sport))
    if not scores:return {"sport":"UNKNOWN","event_context":"Event not identified from snapshot","context_source":"UNRESOLVED"}
    scores.sort(reverse=True)
    sport=scores[0][1]
    return {"sport":sport,"event_context":sport.title()+" market","context_source":"TITLE_DERIVED"}
