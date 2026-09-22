from .official_http import get_official_text
MLS_SCHEDULE_URL = "https://www.mlssoccer.com/news/mls-announces-2026-regular-season-schedule"

def acquire_mls_schedule(timeout=8.0):
    s = get_official_text(MLS_SCHEDULE_URL, timeout=timeout)
    low = s["body"].lower()
    s.update({"provider":"mls_official","league":"MLS","source_authority":"official_league",
              "markers":{"mls":"mls" in low,"schedule":"schedule" in low,"2026":"2026" in low}})
    return s
