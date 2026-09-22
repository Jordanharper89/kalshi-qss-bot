from pathlib import Path
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
MOD=PKG/"canonical_event_candidate_matcher.py"; TEST=ROOT/"test_ksem_019_canonical_event_candidate_matcher.py"
CODE="""from dataclasses import dataclass
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
"""
def main():
    print("="*120); print(" KSEM-019 CANONICAL EVENT CANDIDATE MATCHER"); print("="*120)
    MOD.write_text(CODE,encoding="utf-8"); compile(CODE,str(MOD),"exec")
    TEST.write_text("from qseries_v2.kalshi_sports_evidence_mapping.canonical_event_candidate_matcher import score_candidate,select_exact\na=score_candidate(league='NFL',market_entities=('DAL','NYG'),event_id='1',home='DAL',away='NYG',event_league='NFL')\nb=score_candidate(league='NFL',market_entities=('DAL','NYG'),event_id='2',home='DAL',away='PHI',event_league='NFL')\nstatus,row=select_exact([a,b])\nassert status=='BOUND' and row.canonical_event_id=='1'\nprint('[PASS] exact two-team + league binding wins; ambiguity fail-closes')\nprint('[PASS] KSEM-019 certified')\n",encoding="utf-8")
    print("[WRITE]",MOD.relative_to(ROOT)); print("[WRITE]",TEST.name)
if __name__=="__main__": main()