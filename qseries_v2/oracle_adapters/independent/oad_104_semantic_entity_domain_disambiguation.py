from __future__ import annotations
from dataclasses import dataclass
import re

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

SPORT_SUBDOMAIN_ALIASES={
    "MLB":"baseball",
    "BASEBALL":"baseball",
    "NHL":"hockey",
    "HOCKEY":"hockey",
    "SOCCER":"soccer",
    "FOOTBALL":"football",
    "NFL":"football",
    "NBA":"basketball",
    "WNBA":"basketball",
    "BASKETBALL":"basketball",
    "TENNIS":"tennis",
    "MMA":"combat",
    "UFC":"combat",
    "COMBAT":"combat",
    "ESPORTS":"esports",
    "GOLF":"golf",
    "UNKNOWN":"UNKNOWN",
    "NONE":"UNKNOWN",
    "":"UNKNOWN",
}

@dataclass(frozen=True, slots=True)
class SemanticDisambiguation:
    text: str
    lexical_domain: str
    lexical_subdomain: str
    semantic_domain: str
    semantic_subdomain: str
    state: str
    reason: str

SPORT_STRUCTURE=(
    r"\bwins?\b",r"\bgoals?\b",r"\bpoints?\b",r"\bruns?\b",r"\binnings?\b",
    r"\bsets?\b",r"\bsubmission\b",r"\bdecision\b",r"\bko/tko\b",
)
AMBIGUOUS_ENTITY_PATTERNS=(
    r"\bshanghai\s+port\b",
    r"\bgolden\s+state\b",
    r"\bportland\s+st\.?\b",
)

def canonical_sport_subdomain(value):
    raw=str(value or "").strip()
    return SPORT_SUBDOMAIN_ALIASES.get(raw.upper(), raw.lower() if raw else "UNKNOWN")

def _normalized_subdomain(domain,subdomain):
    domain=str(domain or "").strip()
    subdomain=str(subdomain or "").strip()
    if domain=="sports":
        return canonical_sport_subdomain(subdomain)
    if domain=="financial_markets":
        return subdomain if subdomain not in ("","NONE") else "financial_price"
    return subdomain

def disambiguate_semantic_domain(text,lexical_domain="unknown",guarded_sport="UNKNOWN",lexical_subdomain=""):
    text=str(text or "").strip()
    lexical_domain=str(lexical_domain or "unknown").strip()
    lexical_subdomain=_normalized_subdomain(lexical_domain,lexical_subdomain)
    guarded_sport=str(guarded_sport or "UNKNOWN").strip()

    if guarded_sport not in ("","NONE","UNKNOWN"):
        return SemanticDisambiguation(
            text,lexical_domain,lexical_subdomain,
            "sports",canonical_sport_subdomain(guarded_sport),
            "RESOLVED",
            "guarded sport identity canonicalized and preserved",
        )

    low=text.lower()

    if lexical_domain=="sports":
        return SemanticDisambiguation(
            text,lexical_domain,lexical_subdomain,
            "sports",canonical_sport_subdomain(lexical_subdomain),
            "UPSTREAM_SPORTS_PRESERVED",
            "validated upstream sports subtype canonicalized into semantic sport family",
        )

    if lexical_domain=="financial_markets":
        return SemanticDisambiguation(
            text,lexical_domain,lexical_subdomain,
            "financial_markets",lexical_subdomain or "financial_price",
            "UPSTREAM_FINANCIAL_PRESERVED",
            "validated upstream financial market subtype preserved",
        )

    if any(re.search(p,low,re.I) for p in AMBIGUOUS_ENTITY_PATTERNS):
        return SemanticDisambiguation(
            text,lexical_domain,lexical_subdomain,
            "unknown","",
            "AMBIGUOUS_ENTITY",
            "lexical token occurs inside a named entity; identity not guessed",
        )

    if any(re.search(p,low,re.I) for p in SPORT_STRUCTURE):
        return SemanticDisambiguation(
            text,lexical_domain,lexical_subdomain,
            "sports","UNKNOWN",
            "SPORT_STRUCTURE_ONLY",
            "sports mechanics present without sport identity",
        )

    if lexical_domain!="unknown":
        return SemanticDisambiguation(
            text,lexical_domain,lexical_subdomain,
            lexical_domain,lexical_subdomain,
            "LEXICAL_DOMAIN_ONLY",
            "validated upstream non-sport domain preserved",
        )

    return SemanticDisambiguation(
        text,lexical_domain,lexical_subdomain,
        "unknown","","UNRESOLVED","no safe semantic identity",
    )
