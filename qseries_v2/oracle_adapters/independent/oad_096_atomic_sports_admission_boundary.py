from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_094_expanded_universal_domain_classifier import expanded_domain_classify
from qseries_v2.oracle_adapters.independent.oad_092_expanded_structural_sport_league_resolver import expanded_resolve_sport_league

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class AtomicSportsAdmission:
    ticker:str
    admitted_domain:str
    sport:str
    league:str
    state:str
    evidence:tuple[str,...]

def atomic_sports_admission(market):
    domain = expanded_domain_classify(market)
    ticker = str(market.get("ticker",""))
    if domain.domain != "sports":
        return AtomicSportsAdmission(ticker, domain.domain, "NONE", "NONE", "NOT_SPORTS", domain.evidence)
    resolved = expanded_resolve_sport_league(market)
    if resolved.league in ("", "NONE"):
        return AtomicSportsAdmission(ticker, "sports", "sports_unresolved", "UNKNOWN", "UNRESOLVED", resolved.evidence)
    if resolved.league == "UNKNOWN":
        return AtomicSportsAdmission(ticker, "sports", "sports_unresolved", "UNKNOWN", "UNRESOLVED", resolved.evidence)
    return AtomicSportsAdmission(ticker, "sports", resolved.sport, resolved.league, "RESOLVED", resolved.evidence)

def verify_no_sports_none(rows):
    for row in rows:
        if row.admitted_domain == "sports" and row.league in ("", "NONE"):
            return False
    return True
