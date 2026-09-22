from .official_http import get_official_text
NHL_SCHEDULE_URL = "https://www.nhl.com/schedule"

def acquire_nhl_schedule(timeout=8.0):
    s = get_official_text(NHL_SCHEDULE_URL, timeout=timeout)
    low = s["body"].lower()
    s.update({"provider":"nhl_official","league":"NHL","source_authority":"official_league",
              "markers":{"nhl":"nhl" in low,"schedule":"schedule" in low}})
    return s
