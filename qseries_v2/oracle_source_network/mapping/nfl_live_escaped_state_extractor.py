
import re
from datetime import datetime, timezone
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

_GAME_TIME_PATTERNS = (
    re.compile(r'gameTime\\?":\\?"([^"\\]+)'),
    re.compile(r'gameTime":"([^"]+)'),
)

_LINK_NAME_PATTERNS = (
    re.compile(r'linkName\\?":\\?"([A-Z0-9.\- ]{1,20})\s+@\s+([A-Z0-9.\- ]{1,20})'),
    re.compile(r'linkName":"([A-Z0-9.\- ]{1,20})\s+@\s+([A-Z0-9.\- ]{1,20})'),
)

_HOME_PATTERNS = (
    re.compile(r'homeTeam\\?":\{[^{}]{0,1000}?abbreviation\\?":\\?"([A-Z0-9.\-]{1,12})'),
    re.compile(r'homeTeam":\{[^{}]{0,1000}?abbreviation":"([A-Z0-9.\-]{1,12})'),
)

_AWAY_PATTERNS = (
    re.compile(r'awayTeam\\?":\{[^{}]{0,1000}?abbreviation\\?":\\?"([A-Z0-9.\-]{1,12})'),
    re.compile(r'awayTeam":\{[^{}]{0,1000}?abbreviation":"([A-Z0-9.\-]{1,12})'),
)

_ID_PATTERNS = (
    re.compile(r'sr-element-score-strip-(\d{6,})'),
    re.compile(r'gameId\\?":\\?"?([A-Za-z0-9._:-]{4,})'),
    re.compile(r'gameId":"?([A-Za-z0-9._:-]{4,})'),
)

def _nearest_game_time(body, center, radius=2600):
    a=max(0, center-radius)
    b=min(len(body), center+radius)
    chunk=body[a:b]
    hits=[]
    for pat in _GAME_TIME_PATTERNS:
        for m in pat.finditer(chunk):
            hits.append((abs((a+m.start())-center), m.group(1)))
    if not hits:
        return None
    hits.sort(key=lambda x:x[0])
    return hits[0][1]

def _nearest_id(body, center, radius=1800):
    a=max(0, center-radius)
    b=min(len(body), center+radius)
    chunk=body[a:b]
    hits=[]
    for pat in _ID_PATTERNS:
        for m in pat.finditer(chunk):
            hits.append((abs((a+m.start())-center), m.group(1)))
    if not hits:
        return None
    hits.sort(key=lambda x:x[0])
    return hits[0][1]

def _events_from_link_names(body, observed_at):
    out=[]
    seen=set()
    for pat in _LINK_NAME_PATTERNS:
        for m in pat.finditer(body):
            away=m.group(1).strip()
            home=m.group(2).strip()
            game_time=_nearest_game_time(body, m.start())
            if not game_time:
                continue
            key=(away,home,game_time)
            if key in seen:
                continue
            seen.add(key)
            provider_id=_nearest_id(body,m.start())
            out.append(CanonicalSportsEvent(
                league="NFL",
                season="2026",
                provider="nfl_official",
                home_team=home,
                away_team=away,
                scheduled_start=game_time,
                source_observed_at=observed_at,
                source_authority="official_league",
                provider_event_id=str(provider_id) if provider_id else None,
                event_discriminator=str(provider_id or f"{away}@{home}|{game_time}"),
                status="",
            ))
    return out

def _events_from_team_blocks(body, observed_at):
    out=[]
    seen=set()
    # Anchor on each gameTime occurrence and inspect a bounded local window.
    anchors=[]
    for pat in _GAME_TIME_PATTERNS:
        anchors.extend((m.start(),m.group(1)) for m in pat.finditer(body))
    anchors.sort()

    for pos,game_time in anchors:
        a=max(0,pos-2200)
        b=min(len(body),pos+3200)
        chunk=body[a:b]

        home=None
        away=None
        for pat in _HOME_PATTERNS:
            mh=pat.search(chunk)
            if mh:
                home=mh.group(1).strip()
                break
        for pat in _AWAY_PATTERNS:
            ma=pat.search(chunk)
            if ma:
                away=ma.group(1).strip()
                break

        if not (home and away):
            continue

        key=(away,home,game_time)
        if key in seen:
            continue
        seen.add(key)
        provider_id=_nearest_id(body,pos)

        out.append(CanonicalSportsEvent(
            league="NFL",
            season="2026",
            provider="nfl_official",
            home_team=home,
            away_team=away,
            scheduled_start=game_time,
            source_observed_at=observed_at,
            source_authority="official_league",
            provider_event_id=str(provider_id) if provider_id else None,
            event_discriminator=str(provider_id or f"{away}@{home}|{game_time}"),
            status="",
        ))
    return out

def extract_nfl_live_events(body, observed_at=None):
    observed_at=observed_at or datetime.now(timezone.utc).isoformat()

    # First use the physically observed NFL score-strip "linkName":"AWAY @ HOME"
    # representation. Then augment with physically observed homeTeam/awayTeam blocks.
    candidates=_events_from_link_names(body,observed_at)
    candidates.extend(_events_from_team_blocks(body,observed_at))

    out={}
    for event in candidates:
        out[event.canonical_event_id]=event
    return tuple(out.values())
