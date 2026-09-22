
import html, json, re
from datetime import datetime, timezone
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

def _script_json(body):
    for raw in re.findall(r'<script\b[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', body, re.I|re.S):
        try:
            yield json.loads(html.unescape(raw).strip())
        except Exception:
            continue

def _walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj,list):
        for v in obj:
            yield from _walk(v)

def _pick(d,*keys):
    for k in keys:
        if k in d and d[k] not in (None,""):
            return d[k]
    return None

def _team(x):
    if isinstance(x,str): return x.strip()
    if not isinstance(x,dict): return ""
    for k in ("shortName","name","displayName","teamName","abbreviation"):
        v=x.get(k)
        if isinstance(v,str) and v.strip(): return v.strip()
    return ""

def extract_ncaa_events(body, league, provider, authority, observed_at=None):
    observed_at=observed_at or datetime.now(timezone.utc).isoformat()
    out={}
    for root in _script_json(body):
        for d in _walk(root):
            home=_team(_pick(d,"homeTeam","home","home_team"))
            away=_team(_pick(d,"awayTeam","away","away_team"))
            start=_pick(d,"startTime","startDate","gameTime","start_time","start_date")
            if not (home and away and start):
                continue
            pid=_pick(d,"gameId","eventId","contestId","id","uid")
            event=CanonicalSportsEvent(
                league=league,
                season="2026",
                provider=provider,
                home_team=home,
                away_team=away,
                scheduled_start=str(start),
                source_observed_at=observed_at,
                source_authority=authority,
                provider_event_id=str(pid) if pid is not None else None,
                event_discriminator=str(pid or start),
                status=str(_pick(d,"status","gameStatus","state") or ""),
                home_score=_pick(d,"homeScore","home_score"),
                away_score=_pick(d,"awayScore","away_score"),
            )
            out[event.canonical_event_id]=event
    return tuple(out.values())
