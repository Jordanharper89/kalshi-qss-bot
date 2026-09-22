
import html
import json
import re
from datetime import datetime, timezone
from typing import Iterable

def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(str(s or ""))).strip()

def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)

def _json_candidates(body):
    # Script/data payloads are common on official score/schedule pages.
    for m in re.finditer(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', body, re.I | re.S):
        raw = html.unescape(m.group(1))
        try:
            yield json.loads(raw)
        except Exception:
            pass

def _name(v):
    if isinstance(v, str):
        return _clean(v)
    if isinstance(v, dict):
        for k in ("displayName","fullName","name","shortName","teamName","clubName"):
            if isinstance(v.get(k), str) and _clean(v[k]):
                return _clean(v[k])
    return ""

def _id(v):
    if isinstance(v, dict):
        for k in ("id","eventId","event_id","gameId","game_id","matchId","match_id","uid"):
            if v.get(k) is not None:
                return _clean(v[k])
    return ""

def _start(d):
    for k in ("startTime","start_time","startDate","start_date","date","datetime","kickoff","gameTime"):
        if isinstance(d.get(k), str) and d.get(k):
            return _clean(d[k])
    return None

def _status(d):
    for k in ("status","state","eventStatus","gameStatus"):
        v=d.get(k)
        if isinstance(v, str) and v:
            return _clean(v).upper()
        if isinstance(v, dict):
            for q in ("name","type","state","description"):
                if isinstance(v.get(q), str) and v.get(q):
                    return _clean(v[q]).upper()
    return "SCHEDULED"

def _score(v):
    try:
        if v is None or v == "":
            return None
        return int(float(str(v)))
    except Exception:
        return None

from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

def _extract_dict_event(d, league, provider, season, observed_at, authority):
    home = _name(d.get("homeTeam") or d.get("home_team") or d.get("home"))
    away = _name(d.get("awayTeam") or d.get("away_team") or d.get("away"))
    if not home or not away or home == away:
        return None
    pid = _id(d)
    discriminator = _clean(d.get("round") or d.get("gameNumber") or d.get("week") or "")
    return CanonicalSportsEvent(
        league=league, season=season, provider=provider,
        provider_event_id=pid or None, home_team=home, away_team=away,
        event_discriminator=discriminator, scheduled_start=_start(d),
        source_observed_at=observed_at, source_authority=authority,
        status=_status(d),
        home_score=_score(d.get("homeScore") or d.get("home_score")),
        away_score=_score(d.get("awayScore") or d.get("away_score")),
    )

def extract_basketball_events(body, league, provider, season="2026-27", observed_at=None, authority="official_league"):
    observed_at = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    out, seen = [], set()
    for root in _json_candidates(body):
        for d in _walk(root):
            if not isinstance(d, dict):
                continue
            ev = _extract_dict_event(d, league, provider, season, observed_at, authority)
            if ev and ev.canonical_event_id not in seen:
                seen.add(ev.canonical_event_id); out.append(ev)
    return tuple(out)
