
import json,urllib.request
from datetime import datetime,timezone
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

OPENING_DATE="2026-09-29"
URI=f"https://api-web.nhle.com/v1/schedule/{OPENING_DATE}"

def _get_json(timeout=8.0):
    req=urllib.request.Request(URI,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read()
    return raw,json.loads(raw.decode("utf-8"))

def _games(root):
    if isinstance(root,dict):
        for key in ("gameWeek","games"):
            v=root.get(key)
            if key=="games" and isinstance(v,list):
                for g in v:
                    if isinstance(g,dict): yield g
            elif key=="gameWeek" and isinstance(v,list):
                for day in v:
                    if isinstance(day,dict):
                        for g in day.get("games",[]) if isinstance(day.get("games"),list) else ():
                            if isinstance(g,dict): yield g

def extract_nhl_opening_schedule(observed_at=None,timeout=8.0):
    observed_at=observed_at or datetime.now(timezone.utc).isoformat()
    raw,root=_get_json(timeout)
    out={}
    for g in _games(root):
        gid=g.get("id")
        start=g.get("startTimeUTC")
        home=g.get("homeTeam") if isinstance(g.get("homeTeam"),dict) else {}
        away=g.get("awayTeam") if isinstance(g.get("awayTeam"),dict) else {}
        hn=home.get("abbrev") or home.get("name")
        an=away.get("abbrev") or away.get("name")
        if isinstance(hn,dict): hn=hn.get("default")
        if isinstance(an,dict): an=an.get("default")
        if not (gid and start and hn and an): continue
        e=CanonicalSportsEvent(
            league="NHL",season="2026-27",provider="nhl_official_json",
            home_team=str(hn),away_team=str(an),scheduled_start=str(start),
            source_observed_at=observed_at,source_authority="official_league",
            provider_event_id=str(gid),event_discriminator=str(gid),
            status=str(g.get("gameState") or g.get("gameScheduleState") or ""),
            home_score=home.get("score"),away_score=away.get("score"),
        )
        out[e.canonical_event_id]=e
    return raw,tuple(out.values())
