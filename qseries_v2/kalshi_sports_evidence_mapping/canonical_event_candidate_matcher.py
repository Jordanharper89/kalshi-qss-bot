from dataclasses import dataclass
@dataclass(frozen=True)
class EventCandidate:
    canonical_event_id:str
    league:str
    home:str
    away:str
    score:int
    reasons:tuple
def _n(x): return ' '.join(str(x or '').upper().replace('-',' ').replace('_',' ').split())
def score_candidate(*,league,market_entities,event_id,home,away,event_league):
    reasons=[]; score=0
    if _n(league)==_n(event_league): score+=4; reasons.append('league_exact')
    ents={_n(x) for x in market_entities if _n(x)}
    teams={_n(home),_n(away)}
    hits=len(ents & teams)
    if hits==2: score+=8; reasons.append('two_team_exact')
    elif hits==1: score+=3; reasons.append('one_team_exact')
    return EventCandidate(str(event_id),str(event_league),str(home),str(away),score,tuple(reasons))
def select_exact(candidates):
    ranked=sorted(candidates,key=lambda x:x.score,reverse=True)
    if not ranked or ranked[0].score<12: return ('UNBOUND',None)
    if len(ranked)>1 and ranked[1].score==ranked[0].score: return ('AMBIGUOUS',None)
    return ('BOUND',ranked[0])
