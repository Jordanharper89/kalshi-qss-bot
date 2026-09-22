
from dataclasses import dataclass
from .sports_source_truth import blocked, production_ready

@dataclass(frozen=True, slots=True)
class SourceAdmissionDecision:
    source_id: str
    league: str
    admitted: bool
    status: str
    reason: str
    execution_authority: bool = False

def admission_decisions():
    ready = [
        SourceAdmissionDecision(x.source_id, x.league, True, x.status, "physically certified source")
        for x in production_ready()
    ]
    denied = [
        SourceAdmissionDecision(x.source_id, x.league, False, x.status, x.reason)
        for x in blocked()
    ]
    return tuple(ready + denied)

def admitted_leagues():
    return tuple(x.league for x in admission_decisions() if x.admitted)
