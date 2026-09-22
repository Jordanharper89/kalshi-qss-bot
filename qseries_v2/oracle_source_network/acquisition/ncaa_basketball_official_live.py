
from .official_http import get_official_text

NCAA_D1_MENS_SCOREBOARD_URL = "https://www.ncaa.com/scoreboard/basketball-men/d1"

def acquire_ncaa_d1_mens_scoreboard(timeout=8.0):
    snap = get_official_text(NCAA_D1_MENS_SCOREBOARD_URL, timeout=timeout)
    body = snap["body"]
    low = body.lower()
    markers = {
        "basketball": "basketball" in low,
        "mens": ("men's" in low or "mens" in low or "men" in low),
        "division_i": ("division i" in low or "d1" in low or "di " in low),
        "ncaa": "ncaa" in low,
        "scoreboard_or_scores": ("scoreboard" in low or "scores" in low),
    }
    snap["provider"] = "ncaa_official"
    snap["league"] = "NCAAB"
    snap["source_authority"] = "official_governing_body"
    snap["markers"] = markers
    return snap
