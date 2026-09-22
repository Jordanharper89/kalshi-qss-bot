
import json,urllib.parse,urllib.request
from datetime import datetime,timezone
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

BASE="https://stats-api.mlssoccer.com/matches/seasons/MLS-SEA-0001KA"
PARAMS={
    "match_date[gte]":"2026-08-31",
    "match_date[lte]":"2026-09-13",
    "competition_id":"MLS-COM-000001",
    "per_page":"100",
    "sort":"planned_kickoff_time:asc,home_team_name:asc",
}

def _uri():
    return BASE+"?"+urllib.parse.urlencode(PARAMS)

def _get(timeout=8.0):
    uri=_uri()
    req=urllib.request.Request(uri,headers={"Accept":"application/json","User-Agent":"curl"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read()
    return uri,raw,json.loads(raw.decode("utf-8"))

def _provider_id(match):
    for key in (
        "match_id","id","match_uuid","match_uid","match_code",
        "fixture_id","event_id","game_id"
    ):
        v=match.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None

def probe_and_extract(observed_at=None,timeout=8.0):
    observed_at=observed_at or datetime.now(timezone.utc).isoformat()
    uri,raw,root=_get(timeout)
    schedule=root.get("schedule") if isinstance(root,dict) else None
    if not isinstance(schedule,list):
        return {
            "uri":uri,"bytes":len(raw),"root_keys":tuple(root.keys()) if isinstance(root,dict) else (),
            "schedule_seen":False,"match_keys":(),"events":()
        }

    match_keys=tuple(schedule[0].keys()) if schedule and isinstance(schedule[0],dict) else ()
    out={}
    for m in schedule:
        if not isinstance(m,dict): continue
        start=m.get("planned_kickoff_time")
        home=m.get("home_team_short_name") or m.get("home_team_name")
        away=m.get("away_team_short_name") or m.get("away_team_name")
        if not (start and home and away): continue

        pid=_provider_id(m)
        discr=pid or f"{m.get('match_day','')}|{away}|{home}"

        e=CanonicalSportsEvent(
            league="MLS",
            season="2026",
            provider="mls_official_stats_api",
            home_team=str(home),
            away_team=str(away),
            scheduled_start=str(start),
            source_observed_at=observed_at,
            source_authority="official_league",
            provider_event_id=pid,
            event_discriminator=str(discr),
            status=str(m.get("status") or m.get("match_status") or ""),
        )
        out[e.canonical_event_id]=e

    return {
        "uri":uri,
        "bytes":len(raw),
        "root_keys":tuple(root.keys()) if isinstance(root,dict) else (),
        "schedule_seen":True,
        "schedule_count":len(schedule),
        "match_keys":match_keys,
        "events":tuple(out.values()),
    }
