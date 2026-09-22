
import html,json,re
from datetime import datetime,timezone
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

def _json_docs(body):
    pat=r'<script\b[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>'
    for raw in re.findall(pat,body,re.I|re.S):
        try:
            obj=json.loads(html.unescape(raw).strip())
            if isinstance(obj,dict): yield obj
        except Exception:
            continue

def _team_name(t):
    if not isinstance(t,dict): return ""
    for k in ("nameShort","name10Char","name8Char","name6Char","seoname"):
        v=t.get(k)
        if isinstance(v,str) and v.strip(): return v.strip()
    return ""

def _start(c):
    ep=c.get("startTimeEpoch")
    if isinstance(ep,(int,float)) and ep>0:
        return datetime.fromtimestamp(ep,tz=timezone.utc).isoformat()
    d=c.get("startDate")
    t=c.get("startTime")
    return f"{d} {t}".strip() if d or t else ""

def extract_ncaab_live_events(body,observed_at=None):
    observed_at=observed_at or datetime.now(timezone.utc).isoformat()
    out={}
    schema_seen=False
    for root in _json_docs(body):
        sb=root.get("scoreboard")
        if not isinstance(sb,dict): continue
        if "initialGames" in sb: schema_seen=True
        games=sb.get("initialGames")
        if not isinstance(games,list): continue
        season=str(sb.get("seasonYear") or sb.get("calendarYear") or "2026")
        for c in games:
            if not isinstance(c,dict): continue
            teams=c.get("teams")
            if not isinstance(teams,list): continue
            home=next((x for x in teams if isinstance(x,dict) and x.get("isHome") is True),None)
            away=next((x for x in teams if isinstance(x,dict) and x.get("isHome") is False),None)
            cid=c.get("contestId")
            start=_start(c)
            hn,an=_team_name(home),_team_name(away)
            if not (cid and start and hn and an): continue
            e=CanonicalSportsEvent(
                league="NCAAB",season=season,provider="ncaa_official",
                home_team=hn,away_team=an,scheduled_start=start,
                source_observed_at=observed_at,source_authority="official_governing_body",
                provider_event_id=str(cid),event_discriminator=str(cid),
                status=str(c.get("statusCodeDisplay") or c.get("gameState") or ""),
                home_score=home.get("score") if home else None,
                away_score=away.get("score") if away else None,
            )
            out[e.canonical_event_id]=e
    return tuple(out.values()),schema_seen
