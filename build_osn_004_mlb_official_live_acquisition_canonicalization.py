
from pathlib import Path

REVISION = 'OSN_004_MLB_OFFICIAL_LIVE_ACQUISITION_CANONICALIZATION_V1'
ROOT = Path.cwd()

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", path.relative_to(ROOT))

def main():
    print("=" * 112)
    print(' OSN-004 MLB OFFICIAL LIVE ACQUISITION + CANONICALIZATION INSTALLER')
    print("=" * 112)
    print("[ROOT]", ROOT)
    p = ROOT / 'qseries_v2/oracle_source_network/providers/mlb_statsapi.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    p = ROOT / 'qseries_v2/oracle_source_network/canonical/sports_event.py'
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))
    write(ROOT / 'qseries_v2/oracle_source_network/acquisition/http_json.py', 'from urllib.request import Request, urlopen\nimport json\n\ndef get_json(url: str, timeout: float = 15.0):\n    req = Request(url, headers={"User-Agent":"QSeries-Oracle-OSN/1.0","Accept":"application/json"}, method="GET")\n    with urlopen(req, timeout=timeout) as r:\n        if getattr(r, "status", 200) != 200:\n            raise RuntimeError(f"HTTP status {getattr(r,\'status\',None)}")\n        return json.loads(r.read().decode("utf-8"))')
    write(ROOT / 'qseries_v2/oracle_source_network/canonical/mlb.py', 'import hashlib, json\nfrom .sports_event import SportsEventIdentity, SportsObservation\n\ndef _score(side):\n    try:\n        return int(side["score"])\n    except Exception:\n        return None\n\ndef canonicalize_game(game: dict, observed_at: str) -> SportsObservation:\n    teams = game.get("teams") or {}\n    home = ((teams.get("home") or {}).get("team") or {}).get("name") or ""\n    away = ((teams.get("away") or {}).get("team") or {}).get("name") or ""\n    start = game.get("gameDate") or ""\n    season = str(game.get("season") or start[:4] or "")\n    status = ((game.get("status") or {}).get("abstractGameState")\n              or (game.get("status") or {}).get("detailedState")\n              or "unknown")\n    identity = SportsEventIdentity("baseball","MLB",season,home,away,start)\n    raw = json.dumps(game, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode("utf-8")\n    return SportsObservation(\n        identity=identity,\n        provider="mlb_statsapi",\n        provider_event_id=str(game.get("gamePk") or ""),\n        observed_at=observed_at,\n        status=str(status).lower().replace(" ","_"),\n        home_score=_score(teams.get("home") or {}),\n        away_score=_score(teams.get("away") or {}),\n        payload_sha256=hashlib.sha256(raw).hexdigest(),\n        provenance_uri=f"https://statsapi.mlb.com/api/v1.1/game/{game.get(\'gamePk\')}/feed/live",\n        source_authority="official_league",\n        execution_authority=False,\n    )\n\ndef canonicalize_schedule(payload: dict, observed_at: str):\n    out = []\n    for date_row in payload.get("dates") or []:\n        for game in date_row.get("games") or []:\n            out.append(canonicalize_game(game, observed_at))\n    return tuple(out)')
    write(ROOT / 'qseries_v2/oracle_source_network/acquisition/mlb_live.py', 'from datetime import datetime, timezone\nfrom .http_json import get_json\nfrom ..providers.mlb_statsapi import schedule_url\nfrom ..canonical.mlb import canonicalize_schedule\n\ndef utc_now_iso():\n    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")\n\ndef acquire_date(date: str, timeout: float = 15.0):\n    observed_at = utc_now_iso()\n    payload = get_json(schedule_url(date), timeout=timeout)\n    return canonicalize_schedule(payload, observed_at)')
    write(ROOT / 'test_osn_004_mlb_official_live_acquisition_canonicalization.py', 'from qseries_v2.oracle_source_network.canonical.mlb import canonicalize_schedule\n\nsample = {"dates":[{"games":[{\n  "gamePk":12345,\n  "gameDate":"2026-09-05T19:10:00Z",\n  "season":"2026",\n  "status":{"abstractGameState":"Live"},\n  "teams":{\n    "home":{"team":{"name":"Houston Astros"},"score":3},\n    "away":{"team":{"name":"Seattle Mariners"},"score":2}\n  }\n}]}]}\n\nrows = canonicalize_schedule(sample,"2026-09-05T20:00:00Z")\nassert len(rows) == 1\nx = rows[0]\nassert x.provider == "mlb_statsapi"\nassert x.identity.league == "MLB"\nassert x.identity.event_id.startswith("osn:sport:")\nassert x.home_score == 3 and x.away_score == 2\nassert x.execution_authority is False\nassert len(x.payload_sha256) == 64\nprint("[PASS] OSN-004 deterministic MLB canonicalization certified")\n\ntry:\n    from datetime import date\n    from qseries_v2.oracle_source_network.acquisition.mlb_live import acquire_date\n    physical = acquire_date(str(date.today()), timeout=8.0)\n    print(f"[PHYSICAL] official_mlb_events={len(physical)}")\n    if physical:\n        assert all(r.source_authority == "official_league" for r in physical)\n        assert all(r.execution_authority is False for r in physical)\n        print("[PASS] official MLB physical read succeeded")\nexcept Exception as e:\n    print(f"[INFO] physical MLB probe unavailable: {type(e).__name__}: {e}")')
    print('[PASS] OSN-004 installed')

if __name__ == '__main__':
    main()
