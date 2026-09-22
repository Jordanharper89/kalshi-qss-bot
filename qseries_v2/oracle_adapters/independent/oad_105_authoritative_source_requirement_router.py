from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

SPORT_ALIASES={
    "MLB":"baseball","BASEBALL":"baseball",
    "NHL":"hockey","HOCKEY":"hockey",
    "SOCCER":"soccer",
    "NFL":"football","FOOTBALL":"football",
    "NBA":"basketball","WNBA":"basketball","BASKETBALL":"basketball",
    "TENNIS":"tennis",
    "MMA":"combat","UFC":"combat","COMBAT":"combat",
    "ESPORTS":"esports","GOLF":"golf",
    "UNKNOWN":"UNKNOWN","NONE":"UNKNOWN","":"UNKNOWN",
}

@dataclass(frozen=True, slots=True)
class SourceRequirement:
    domain: str
    subdomain: str
    state: str
    authoritative_source_families: tuple[str,...]

SPORT_SOURCES={
    "baseball":("Official league/game/stat sources",),
    "soccer":("Competition/club official match sources",),
    "tennis":("ATP/WTA/official tournament sources",),
    "combat":("UFC/commission/promotion official sources",),
    "golf":("Official tour/tournament sources",),
    "esports":("Official tournament/operator sources",),
    "hockey":("NHL/official league game-stat sources",),
    "basketball":("NBA/WNBA/NCAA official game-stat sources",),
    "football":("NFL/NCAA official game-stat sources",),
    "UNKNOWN":("Sport-specific authoritative source unresolved",),
}
DOMAIN_SOURCES={
    "financial_markets":("Independent underlying asset/reference-price source",),
    "financial_price":("Independent underlying asset/reference-price source",),
    "crypto":("Independent exchange/chain reference sources",),
    "macroeconomics":("BLS","BEA","Federal Reserve/FRED"),
    "politics_elections":("Official election authorities","FEC"),
    "weather":("NWS/NOAA",),
    "energy_commodities":("EIA","USDA/official commodity sources"),
    "legal_regulatory":("Federal Register","Official courts/regulators"),
    "health":("CDC","FDA"),
    "transport":("FAA","TSA","Maritime/port authorities"),
    "science_space":("NASA/official science agencies",),
    "geopolitics":("State/Defense/UN official sources",),
}

def canonical_sport_subdomain(value):
    raw=str(value or "").strip()
    return SPORT_ALIASES.get(raw.upper(),raw.lower() if raw else "UNKNOWN")

def assign_source_requirement(domain,subdomain="",state="UNRESOLVED"):
    domain=str(domain or "unknown").strip()
    subdomain=str(subdomain or "").strip()
    state=str(state or "UNRESOLVED").strip()

    if domain=="sports":
        subdomain=canonical_sport_subdomain(subdomain)
        fam=SPORT_SOURCES.get(subdomain)
        if fam is None:
            return SourceRequirement(domain,subdomain,"UNMAPPED",())
        return SourceRequirement(domain,subdomain,state,fam)

    if domain=="financial_markets":
        subdomain=subdomain if subdomain not in ("","NONE") else "financial_price"
        return SourceRequirement(domain,subdomain,state,DOMAIN_SOURCES["financial_markets"])

    if domain in DOMAIN_SOURCES:
        return SourceRequirement(domain,subdomain,state,DOMAIN_SOURCES[domain])

    return SourceRequirement(domain,subdomain,"UNMAPPED",())
