
import hashlib
import json
from .sports_event import SportsEventIdentity, SportsObservation

def _score(side):
    try:
        return int(side["score"])
    except Exception:
        return None

def canonicalize_game(game: dict, observed_at: str) -> SportsObservation:
    teams = game.get("teams") or {}
    home_side = teams.get("home") or {}
    away_side = teams.get("away") or {}
    home = (home_side.get("team") or {}).get("name") or ""
    away = (away_side.get("team") or {}).get("name") or ""
    start = game.get("gameDate") or ""
    season = str(game.get("season") or start[:4] or "")
    status_obj = game.get("status") or {}
    status = status_obj.get("abstractGameState") or status_obj.get("detailedState") or "unknown"

    if not game.get("gamePk"):
        raise ValueError("MLB game missing gamePk")
    if not start:
        raise ValueError("MLB game missing gameDate")
    if not home or not away:
        raise ValueError("MLB game missing participant identity")

    identity = SportsEventIdentity("baseball", "MLB", season, home, away, start)
    raw = json.dumps(game, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    return SportsObservation(
        identity=identity,
        provider="mlb_statsapi",
        provider_event_id=str(game["gamePk"]),
        observed_at=observed_at,
        status=str(status).lower().replace(" ", "_"),
        home_score=_score(home_side),
        away_score=_score(away_side),
        payload_sha256=hashlib.sha256(raw).hexdigest(),
        provenance_uri=f"https://statsapi.mlb.com/api/v1.1/game/{game['gamePk']}/feed/live",
        source_authority="official_league",
        execution_authority=False,
    )

def canonicalize_schedule(payload: dict, observed_at: str):
    out = []
    for date_row in payload.get("dates") or []:
        for game in date_row.get("games") or []:
            out.append(canonicalize_game(game, observed_at))
    return tuple(out)
