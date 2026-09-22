
import json,urllib.request
from datetime import datetime,timezone
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent
BOOT="https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES="https://fantasy.premierleague.com/api/fixtures/"

def _get(uri,timeout=8.0):
    req=urllib.request.Request(uri,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
    return raw,json.loads(raw.decode("utf-8"))

def extract_epl_fixtures(observed_at=None,timeout=8.0):
    observed_at=observed_at or datetime.now(timezone.utc).isoformat()
    braw,boot=_get(BOOT,timeout)
    fraw,fixtures=_get(FIXTURES,timeout)
    teams={int(t["id"]):t["name"] for t in boot.get("teams",[]) if isinstance(t,dict) and t.get("id") and t.get("name")}
    out={}
    for f in fixtures if isinstance(fixtures,list) else ():
        if not isinstance(f,dict): continue
        fid=f.get("id"); start=f.get("kickoff_time")
        h=teams.get(f.get("team_h")); a=teams.get(f.get("team_a"))
        if not(fid and start and h and a): continue
        status="finished" if f.get("finished") else ("started" if f.get("started") else "scheduled")
        e=CanonicalSportsEvent(
            league="EPL",season="2026-27",provider="premier_league_fpl_official",
            home_team=h,away_team=a,scheduled_start=start,
            source_observed_at=observed_at,source_authority="official_league",
            provider_event_id=str(fid),event_discriminator=str(f.get("event") or fid),
            status=status,home_score=f.get("team_h_score"),away_score=f.get("team_a_score"),
        )
        out[e.canonical_event_id]=e
    return braw,fraw,tuple(out.values())
