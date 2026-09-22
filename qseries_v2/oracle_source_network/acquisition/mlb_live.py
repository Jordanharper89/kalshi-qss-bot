
from datetime import datetime, timezone
from .http_json import get_json
from ..providers.mlb_statsapi import schedule_url
from ..canonical.mlb import canonicalize_schedule

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def acquire_date(date: str, timeout: float = 8.0):
    observed_at = utc_now_iso()
    payload = get_json(schedule_url(date), timeout=timeout)
    return canonicalize_schedule(payload, observed_at)
