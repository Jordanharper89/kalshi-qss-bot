
import html
import json
import re
from datetime import datetime, timezone
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

def _application_json(body):
    pattern=r'<script\b[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>'
    for raw in re.findall(pattern, body, re.I|re.S):
        text=html.unescape(raw).strip()
        if not text:
            continue
        try:
            obj=json.loads(text)
            if isinstance(obj,dict):
                yield obj
        except Exception:
            continue

def _find_scoreboard(root):
    sb=root.get("scoreboard")
    return sb if isinstance(sb,dict) else None

def _team_name(team):
    if not isinstance(team,dict):
        return ""
    for key in ("nameShort","name10Char","name8Char","name6Char","seoname"):
        v=team.get(key)
        if isinstance(v,str) and v.strip():
            return v.strip()
    return ""

def _split_teams(teams):
    home=None
    away=None
    for team in teams if isinstance(teams,list) else ():
        if not isinstance(team,dict):
            continue
        if team.get("isHome") is True:
            home=team
        elif team.get("isHome") is False:
            away=team
    return home,away

def _scheduled_start(contest):
    epoch=contest.get("startTimeEpoch")
    if isinstance(epoch,(int,float)) and epoch > 0:
        try:
            return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        except Exception:
            pass

    date=contest.get("startDate")
    time=contest.get("startTime")
    if isinstance(date,str) and isinstance(time,str) and date.strip() and time.strip():
        # Preserve official display values if no usable epoch exists.
        return f"{date.strip()} {time.strip()}"

    if isinstance(date,str) and date.strip():
        return date.strip()

    return ""

def extract_ncaaf_live_events(body, observed_at=None):
    observed_at=observed_at or datetime.now(timezone.utc).isoformat()
    out={}

    for root in _application_json(body):
        scoreboard=_find_scoreboard(root)
        if not scoreboard:
            continue

        games=scoreboard.get("initialGames")
        if not isinstance(games,list):
            continue

        season=str(scoreboard.get("seasonYear") or "2026")

        for contest in games:
            if not isinstance(contest,dict):
                continue
            if contest.get("__typename") not in (None,"Contest"):
                continue

            contest_id=contest.get("contestId")
            start=_scheduled_start(contest)
            home,away=_split_teams(contest.get("teams"))

            home_name=_team_name(home)
            away_name=_team_name(away)

            if not (contest_id and start and home_name and away_name):
                continue

            event=CanonicalSportsEvent(
                league="NCAAF",
                season=season,
                provider="ncaa_official",
                home_team=home_name,
                away_team=away_name,
                scheduled_start=start,
                source_observed_at=observed_at,
                source_authority="official_governing_body",
                provider_event_id=str(contest_id),
                event_discriminator=str(contest_id),
                status=str(
                    contest.get("statusCodeDisplay")
                    or contest.get("gameState")
                    or contest.get("currentPeriod")
                    or ""
                ),
                home_score=home.get("score") if isinstance(home,dict) else None,
                away_score=away.get("score") if isinstance(away,dict) else None,
            )
            out[event.canonical_event_id]=event

    return tuple(out.values())
