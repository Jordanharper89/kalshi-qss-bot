from dataclasses import dataclass
@dataclass(frozen=True)
class SportsMarketAdmission:
 ticker:str; admitted:bool; sport:str|None; league:str|None; reasons:tuple; execution_authority:bool=False
def admit_from_classification(ticker,*,is_sports,sport=None,league=None,reasons=()):
 ok=bool(ticker and is_sports and (sport or league)); rs=tuple(reasons)
 if is_sports and not ok: rs=rs+('SPORT_OR_LEAGUE_UNRESOLVED',)
 return SportsMarketAdmission(str(ticker),ok,sport,league,rs,False)
