
from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class SportsExtractionTruth:
    league:str
    state:str
    admitted:bool
    reason:str
    execution_authority:bool=False

def rows():
    return (
        SportsExtractionTruth("NFL","PHYSICAL_EXTRACTING",True,"OSN-044 repaired extractor produced 32 unique live events"),
        SportsExtractionTruth("NCAAF","PHYSICAL_EXTRACTING",True,"OSN-045 exact scoreboard extractor produced 99 unique live events"),
        SportsExtractionTruth("NBA","PHYSICAL_EXTRACTING",True,"OSN-036 positive-control physical extraction retained"),
        SportsExtractionTruth("NCAAB","EXACT_EXTRACTOR_READY_CURRENT_PAGE_EMPTY",False,"Exact scoreboard contract proven; current official page has no initialGames records"),
        SportsExtractionTruth("NHL","SOURCE_EVENT_SURFACE_REQUIRED",False,"Official schedule HTML shell exposed zero structured event objects"),
        SportsExtractionTruth("MLS","SOURCE_EVENT_SURFACE_REQUIRED",False,"Current acquisition was schedule announcement article, not production event feed"),
        SportsExtractionTruth("EPL","SOURCE_EVENT_SURFACE_REQUIRED",False,"Current acquisition was fixture announcement article, not production event feed"),
        SportsExtractionTruth("UCL","BLOCKED",False,"Official UEFA runtime acquisition remains blocked"),
    )
