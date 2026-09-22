
"""OSN-006 final clean Kalshi sports demand resolver."""
import re
from collections.abc import Mapping

REVISION = "OSN_006_KALSHI_SPORTS_DEMAND_FINAL_CLEAN_V1"
READ_ONLY = True
EXECUTION_AUTHORITY = False

LEAGUE_PATTERNS = (
    ("MLB", (r"\bmlb\b", r"major league baseball", r"\bbaseball\b")),
    ("NFL", (r"\bnfl\b", r"national football league")),
    ("NCAAF", (r"\bncaaf\b", r"college football", r"ncaa football")),
    ("NBA", (r"\bnba\b", r"national basketball association")),
    ("NCAAB", (r"\bncaab\b", r"college basketball", r"ncaa basketball")),
    ("NHL", (r"\bnhl\b", r"national hockey league")),
    ("MLS", (r"\bmls\b", r"major league soccer")),
    ("EPL", (r"\bepl\b", r"premier league")),
    ("UCL", (r"\bucl\b", r"champions league")),
)

def _flatten_text(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        out = []
        for k, v in value.items():
            out.extend(_flatten_text(k))
            out.extend(_flatten_text(v))
        return out
    if isinstance(value, (list, tuple, set)):
        out = []
        for item in value:
            out.extend(_flatten_text(item))
        return out
    return [str(value)]

def detect_league(record):
    text = " ".join(_flatten_text(record)).lower()
    for league, patterns in LEAGUE_PATTERNS:
        if any(re.search(p, text, re.I) for p in patterns):
            return league
    return "UNKNOWN"

def resolve_records(records):
    counts = {}
    total = 0
    for record in records:
        total += 1
        league = detect_league(record)
        counts[league] = counts.get(league, 0) + 1
    return {
        "live_sports_markets_evaluated": total,
        "league_counts": dict(sorted(counts.items())),
        "read_only": True,
        "execution_authority": False,
    }
