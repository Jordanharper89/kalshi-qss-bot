
from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class ExtractionAdmission:
    league: str
    status: str
    events: int
    admitted: bool
    reason: str
    execution_authority: bool = False

def decide(result):
    if result.status=="EXTRACTING" and result.events>0 and result.unique_ids==result.events and result.read_only:
        return ExtractionAdmission(result.league,result.status,result.events,True,"live canonical events physically extracted")
    return ExtractionAdmission(result.league,result.status,result.events,False,"not admitted until live official payload yields canonical events")
