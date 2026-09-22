from dataclasses import dataclass
TYPES=frozenset(('GAME_WINNER', 'TEAM_TOTAL', 'GAME_TOTAL', 'SPREAD_MARGIN', 'PLAYER_STAT', 'TEAM_STAT', 'SCORING_OCCURRENCE', 'PLAYOFF_QUALIFICATION', 'CHAMPIONSHIP_FUTURE', 'SEASON_WINS', 'STANDINGS_RANKING', 'TOURNAMENT_ADVANCEMENT', 'AWARD', 'OTHER'))
@dataclass(frozen=True)
class SportsProposition:
 ticker:str; proposition_type:str; subjects:tuple; condition:str; resolved:bool; reasons:tuple; execution_authority:bool=False
def proposition(ticker,proposition_type,subjects=(),condition='',reasons=()):
 pt=str(proposition_type or '').upper(); rs=tuple(reasons); ok=bool(ticker and pt in TYPES and tuple(subjects) and str(condition).strip())
 if pt not in TYPES: rs=rs+('UNSUPPORTED_PROPOSITION_TYPE',)
 return SportsProposition(str(ticker),pt,tuple(subjects),str(condition),ok,rs,False)
