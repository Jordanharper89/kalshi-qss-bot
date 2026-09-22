from __future__ import annotations
import json
from urllib.request import Request, urlopen
from .oad_107_authoritative_sports_source_foundation import build_observation, utcnow_iso

PROVIDER="statsapi.mlb.com"
BASE="https://statsapi.mlb.com/api/v1"

def fetch_mlb_schedule(*, date=None, timeout_seconds=20):
    url=BASE+"/schedule?sportId=1"
    if date: url += "&date="+str(date)
    req=Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})
    with urlopen(req,timeout=timeout_seconds) as r:
        data=json.loads(r.read().decode("utf-8"))
    obs=[]
    for d in data.get("dates",[]):
        for g in d.get("games",[]):
            gid=g.get("gamePk")
            teams=g.get("teams",{})
            away=((teams.get("away") or {}).get("team") or {}).get("name","")
            home=((teams.get("home") or {}).get("team") or {}).get("name","")
            subject=f"{away} at {home}".strip()
            obs.append(build_observation(
                source_id=f"mlb:game:{gid}", provider=PROVIDER, sport_family="baseball",
                observation_type="official_game_schedule_state", subject=subject,
                observed_at=utcnow_iso(), source_url=url, payload=g))
    return tuple(obs)
