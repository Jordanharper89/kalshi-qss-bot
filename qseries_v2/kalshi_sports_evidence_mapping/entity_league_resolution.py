from dataclasses import dataclass
@dataclass(frozen=True)
class EntityLeagueResolution:
 ticker:str; league:str|None; entities:tuple; resolved:bool; ambiguity:tuple; execution_authority:bool=False
def resolve_from_existing(ticker,*,league=None,entities=(),ambiguity=()):
 es=tuple(dict.fromkeys(str(x).strip() for x in entities if str(x).strip())); amb=tuple(ambiguity); ok=bool(ticker and league and es and not amb)
 return EntityLeagueResolution(str(ticker),league,es,ok,amb,False)
