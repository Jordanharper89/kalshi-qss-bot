
import re
from .official_http import get_official_text

NCAA_FBS_SCOREBOARD_URL = "https://www.ncaa.com/scoreboard/football/fbs"

def acquire_ncaa_fbs_scoreboard(timeout=8.0):
    snap = get_official_text(NCAA_FBS_SCOREBOARD_URL, timeout=timeout)
    body = snap["body"]
    low = body.lower()
    markers = {
        "football": "football" in low,
        "fbs": "fbs" in low,
        "ncaa": "ncaa" in low,
        "scoreboard": "scoreboard" in low or "scores" in low,
    }
    snap["provider"] = "ncaa_official"
    snap["league"] = "NCAAF"
    snap["source_authority"] = "official_governing_body"
    snap["markers"] = markers
    return snap
