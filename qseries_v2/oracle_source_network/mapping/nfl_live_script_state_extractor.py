
import json, re
from datetime import datetime, timezone
from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent

def _iter_json_fragments(body):
    # NFL page contains escaped application state rather than plain application/json script tags.
    # We search bounded object-like regions around known game-bearing keys and decode only valid JSON.
    needles = ('"gameTime"', '\\"gameTime\\"')
    seen=set()
    for needle in needles:
        start=0
        while True:
            idx=body.find(needle,start)
            if idx < 0:
                break
            a=max(0, body.rfind("{", 0, idx))
            # bounded forward scan for a plausible object terminator
            for b in range(idx+len(needle), min(len(body), idx+6000)):
                if body[b] == "}":
                    raw=body[a:b+1]
                    candidates=[raw, raw.replace('\\"','"')]
                    for c in candidates:
                        if c in seen:
                            continue
                        seen.add(c)
                        try:
                            obj=json.loads(c)
                            if isinstance(obj,dict):
                                yield obj
                        except Exception:
                            pass
            start=idx+len(needle)

def _walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj,list):
        for v in obj:
            yield from _walk(v)

def _team_name(x):
    if isinstance(x,str):
        return x.strip()
    if not isinstance(x,dict):
        return ""
    for k in ("abbreviation","displayName","fullName","name","teamName"):
        v=x.get(k)
        if isinstance(v,str) and v.strip():
            return v.strip()
    return ""

def extract_nfl_live_events(body, observed_at=None):
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    out={}
    for root in _iter_json_fragments(body):
        for obj in _walk(root):
            game_time=obj.get("gameTime") or obj.get("startTime")
            home=_team_name(obj.get("homeTeam"))
            away=_team_name(obj.get("awayTeam"))
            if not (game_time and home and away):
                continue
            provider_id = (
                obj.get("gameId") or obj.get("eventId") or obj.get("id")
                or obj.get("gameKey") or obj.get("uid")
            )
            event=CanonicalSportsEvent(
                league="NFL",
                season="2026",
                provider="nfl_official",
                home_team=home,
                away_team=away,
                scheduled_start=str(game_time),
                source_observed_at=observed_at,
                source_authority="official_league",
                provider_event_id=str(provider_id) if provider_id is not None else None,
                event_discriminator=str(provider_id or game_time),
                status=str(obj.get("status") or obj.get("gameStatus") or ""),
                home_score=obj.get("homeScore"),
                away_score=obj.get("awayScore"),
            )
            out[event.canonical_event_id]=event
    return tuple(out.values())
