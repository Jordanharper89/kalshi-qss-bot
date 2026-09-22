from __future__ import annotations
import json
from urllib.request import Request, urlopen
from .oad_107_authoritative_sports_source_foundation import build_observation, utcnow_iso

PROVIDER="api-web.nhle.com"
BASE="https://api-web.nhle.com/v1"

def fetch_nhl_schedule(*, date, timeout_seconds=20):
    url=f"{BASE}/schedule/{date}"
    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})
    with urlopen(req,timeout=timeout_seconds) as r:
        data=json.loads(r.read().decode("utf-8"))
    obs=[]
    for week in data.get("gameWeek",[]):
        for g in week.get("games",[]):
            gid=g.get("id")
            away=((g.get("awayTeam") or {}).get("placeName") or {}).get("default","")
            home=((g.get("homeTeam") or {}).get("placeName") or {}).get("default","")
            subject=f"{away} at {home}".strip()
            obs.append(build_observation(
                source_id=f"nhl:game:{gid}", provider=PROVIDER, sport_family="hockey",
                observation_type="official_game_schedule_state", subject=subject,
                observed_at=utcnow_iso(), source_url=url, payload=g))
    return tuple(obs)
