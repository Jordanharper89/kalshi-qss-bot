from dataclasses import dataclass
from types import MappingProxyType
OSR_022_BUILD_ID="OSR-022"; OSR_022_REVISION="OSR_022_GAME_THEORETIC_INTERACTION_ANALYSIS_V1"
@dataclass(frozen=True)
class StrategyPayoff:
    agent_id:str; strategy_id:str; opponent_strategy_id:str; payoff:float
@dataclass(frozen=True)
class GameInteraction:
    best_responses:tuple[tuple[str,str],...]; equilibrium_pairs:tuple[tuple[str,str],...]
def analyze_two_agent_game(a_rows,b_rows):
    A=tuple(a_rows);B=tuple(b_rows)
    if not A or not B: raise ValueError("payoffs required")
    a_best={o:sorted((x for x in A if x.opponent_strategy_id==o),key=lambda x:(-x.payoff,x.strategy_id))[0].strategy_id for o in {x.opponent_strategy_id for x in A}}
    b_best={o:sorted((x for x in B if x.opponent_strategy_id==o),key=lambda x:(-x.payoff,x.strategy_id))[0].strategy_id for o in {x.opponent_strategy_id for x in B}}
    eq=tuple(sorted((a,b) for b,a in a_best.items() if b_best.get(a)==b))
    br=tuple(sorted(tuple(("A:"+k,v) for k,v in a_best.items())+tuple(("B:"+k,v) for k,v in b_best.items())))
    return GameInteraction(br,eq)
def build_osr_022_certification_manifest(): return MappingProxyType({"build_id":OSR_022_BUILD_ID,"revision":OSR_022_REVISION,"game":"two_agent_best_response","execution":False})
def verify_osr_022_game_theoretic_interaction_analysis():
    A=(StrategyPayoff("A","C","C",3),StrategyPayoff("A","D","C",5),StrategyPayoff("A","C","D",0),StrategyPayoff("A","D","D",1))
    B=(StrategyPayoff("B","C","C",3),StrategyPayoff("B","D","C",5),StrategyPayoff("B","C","D",0),StrategyPayoff("B","D","D",1))
    return ("D","D") in analyze_two_agent_game(A,B).equilibrium_pairs
