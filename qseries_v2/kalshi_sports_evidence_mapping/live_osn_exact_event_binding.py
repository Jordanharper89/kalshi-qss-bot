import re
from dataclasses import dataclass,asdict
from qseries_v2.oracle_source_network.providers.uniform_sports_provider import acquire_canonical_events

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False
ADMITTED=("NFL","NCAAF","NBA","NHL","MLS","EPL")

@dataclass(frozen=True)
class LiveOSNEventBinding:
    market_ticker:str
    event_ticker:str
    league:str|None
    canonical_event_id:str|None
    home_team:str|None
    away_team:str|None
    status:str
    score:int
    reasons:tuple
    execution_authority:bool=False

def _tokens(v):
    stop={"THE","AT","VS","V","TO","WIN","GAME","MATCH","OVER","UNDER","BY","POINTS","GOALS","RUNS","REG","TIME"}
    return {x for x in re.findall(r"[A-Z0-9]+",str(v or "").upper()) if len(x)>1 and x not in stop}

def _score(context,event):
    if str(context.get("league") or "").upper()!=str(event.league).upper():
        return 0,("league_mismatch",)
    text=" ".join(str(context.get(k) or "") for k in ("title","subtitle","yes_sub_title","no_sub_title"))
    mt=_tokens(text)
    home=_tokens(event.home_team); away=_tokens(event.away_team)
    hh=len(mt & home); ah=len(mt & away)
    score=4
    reasons=["league_exact"]
    if hh: score+=4; reasons.append("home_identity_overlap")
    if ah: score+=4; reasons.append("away_identity_overlap")
    if hh and ah: score+=4; reasons.append("two_sided_event_identity")
    return score,tuple(reasons)

def bind_context(context,events):
    league=context.get("league")
    if league not in ADMITTED:
        return LiveOSNEventBinding(context["market_ticker"],context.get("event_ticker",""),league,None,None,None,"SOURCE_GAP",0,("league_not_admitted",),False)
    ranked=[]
    for ev in events:
        score,reasons=_score(context,ev)
        if score:
            ranked.append((score,ev,reasons))
    ranked.sort(key=lambda x:(-x[0],str(x[1].canonical_event_id)))
    if not ranked or ranked[0][0]<12:
        return LiveOSNEventBinding(context["market_ticker"],context.get("event_ticker",""),league,None,None,None,"SOURCE_GAP",ranked[0][0] if ranked else 0,("no_exact_event_identity",),False)
    top=ranked[0]
    ties=[x for x in ranked if x[0]==top[0]]
    if len(ties)>1:
        return LiveOSNEventBinding(context["market_ticker"],context.get("event_ticker",""),league,None,None,None,"AMBIGUOUS",top[0],("multiple_equal_event_candidates",),False)
    ev=top[1]
    return LiveOSNEventBinding(context["market_ticker"],context.get("event_ticker",""),league,ev.canonical_event_id,ev.home_team,ev.away_team,"EXACT_BOUND",top[0],top[2],False)

def run_binding(context_rows,root=None,timeout=15):
    needed=sorted({str(x.get("league") or "") for x in context_rows if x.get("league") in ADMITTED})
    events={}
    for league in needed:
        result=acquire_canonical_events(league,timeout=timeout,root=root)
        events[league]=tuple(result.events)
    return tuple(bind_context(x,events.get(x.get("league"),())) for x in context_rows),events
