from __future__ import annotations
from dataclasses import dataclass
import re

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class SportsEntityType:
    text:str
    entity_type:str
    structural_class:str
    evidence:tuple[str,...]

# Important: numeric '+' props must NOT use a trailing \b after '+'
# because '+' is itself a non-word character. Use an explicit right-edge lookahead.
PROP_PATTERNS=(
    ("player_prop", r"(?<!\d)\d+(?:\.\d+)?\+(?=\s|$|[,;/)])"),
    ("spread_or_handicap", r"\bwins?\s+(?:1h\s+)?by\s+over\s+\d"),
    ("total", r"\bover\s+\d+(?:\.\d+)?\s+(?:points|runs|goals)\s+scored\b"),
    ("baseball_innings", r"\bfirst\s+5\s+innings\b"),
    ("soccer_btts", r"\bboth\s+teams\s+to\s+score\b"),
)

TEAM_HINTS=(
    " fc"," united"," city"," state"," st."," university",
    " tigers"," fighters"," heroes"," dinos"," esports"," team "
)

def recognize_sports_entity_type(text):
    raw=str(text or "").strip()
    low=" "+raw.lower()+" "
    for structural_class, pattern in PROP_PATTERNS:
        if re.search(pattern, raw, re.I):
            return SportsEntityType(
                raw,
                "STRUCTURED_MARKET_LEG",
                structural_class,
                (structural_class,),
            )

    if "/" in raw and len(raw.split("/"))==2:
        return SportsEntityType(
            raw,
            "PAIR_OR_DOUBLES",
            "participant_pair",
            ("slash_pair",),
        )

    if any(hint in low for hint in TEAM_HINTS):
        return SportsEntityType(
            raw,
            "TEAM_OR_CLUB",
            "named_competitor",
            ("team_structure",),
        )

    words=re.findall(r"[A-Za-zÀ-ÿ'.-]+", raw)
    if (
        2 <= len(words) <= 5
        and not re.search(
            r"\b(over|under|target|price|points|runs|goals|wins|tie)\b",
            raw,
            re.I,
        )
    ):
        return SportsEntityType(
            raw,
            "NAMED_COMPETITOR",
            "participant_candidate",
            ("proper_name_shape",),
        )

    return SportsEntityType(raw, "UNRESOLVED", "unknown", ())
