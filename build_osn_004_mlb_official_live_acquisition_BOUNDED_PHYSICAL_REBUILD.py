from pathlib import Path

REVISION = "OSN_004_MLB_OFFICIAL_LIVE_ACQUISITION_BOUNDED_PHYSICAL_REBUILD_V1"
ROOT = Path.cwd()

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("=" * 118)
    print(" OSN-004 MLB OFFICIAL LIVE ACQUISITION — BOUNDED PHYSICAL REBUILD INSTALLER")
    print("=" * 118)
    print("[ROOT]", ROOT)

    require("qseries_v2/oracle_source_network/providers/mlb_statsapi.py")
    require("qseries_v2/oracle_source_network/canonical/sports_event.py")
    require("qseries_v2/oracle_source_network/foundation.py")

    write("qseries_v2/oracle_source_network/acquisition/http_json.py", '\nfrom urllib.request import Request, urlopen\nimport json\n\nDEFAULT_TIMEOUT_SECONDS = 8.0\n\ndef get_json(url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS):\n    timeout = float(timeout)\n    if timeout <= 0 or timeout > 20:\n        raise ValueError("OSN HTTP timeout must be >0 and <=20 seconds")\n    req = Request(\n        url,\n        headers={\n            "User-Agent": "QSeries-Oracle-OSN/1.0",\n            "Accept": "application/json",\n            "Connection": "close",\n        },\n        method="GET",\n    )\n    with urlopen(req, timeout=timeout) as r:\n        status = getattr(r, "status", 200)\n        if status != 200:\n            raise RuntimeError(f"HTTP status {status}")\n        return json.loads(r.read().decode("utf-8"))\n')
    write("qseries_v2/oracle_source_network/canonical/mlb.py", '\nimport hashlib\nimport json\nfrom .sports_event import SportsEventIdentity, SportsObservation\n\ndef _score(side):\n    try:\n        return int(side["score"])\n    except Exception:\n        return None\n\ndef canonicalize_game(game: dict, observed_at: str) -> SportsObservation:\n    teams = game.get("teams") or {}\n    home_side = teams.get("home") or {}\n    away_side = teams.get("away") or {}\n    home = (home_side.get("team") or {}).get("name") or ""\n    away = (away_side.get("team") or {}).get("name") or ""\n    start = game.get("gameDate") or ""\n    season = str(game.get("season") or start[:4] or "")\n    status_obj = game.get("status") or {}\n    status = status_obj.get("abstractGameState") or status_obj.get("detailedState") or "unknown"\n\n    if not game.get("gamePk"):\n        raise ValueError("MLB game missing gamePk")\n    if not start:\n        raise ValueError("MLB game missing gameDate")\n    if not home or not away:\n        raise ValueError("MLB game missing participant identity")\n\n    identity = SportsEventIdentity("baseball", "MLB", season, home, away, start)\n    raw = json.dumps(game, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")\n\n    return SportsObservation(\n        identity=identity,\n        provider="mlb_statsapi",\n        provider_event_id=str(game["gamePk"]),\n        observed_at=observed_at,\n        status=str(status).lower().replace(" ", "_"),\n        home_score=_score(home_side),\n        away_score=_score(away_side),\n        payload_sha256=hashlib.sha256(raw).hexdigest(),\n        provenance_uri=f"https://statsapi.mlb.com/api/v1.1/game/{game[\'gamePk\']}/feed/live",\n        source_authority="official_league",\n        execution_authority=False,\n    )\n\ndef canonicalize_schedule(payload: dict, observed_at: str):\n    out = []\n    for date_row in payload.get("dates") or []:\n        for game in date_row.get("games") or []:\n            out.append(canonicalize_game(game, observed_at))\n    return tuple(out)\n')
    write("qseries_v2/oracle_source_network/acquisition/mlb_live.py", '\nfrom datetime import datetime, timezone\nfrom .http_json import get_json\nfrom ..providers.mlb_statsapi import schedule_url\nfrom ..canonical.mlb import canonicalize_schedule\n\ndef utc_now_iso():\n    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")\n\ndef acquire_date(date: str, timeout: float = 8.0):\n    observed_at = utc_now_iso()\n    payload = get_json(schedule_url(date), timeout=timeout)\n    return canonicalize_schedule(payload, observed_at)\n')
    write("test_osn_004_mlb_official_live_acquisition_canonicalization.py", '\nimport subprocess\nimport sys\n\nfrom qseries_v2.oracle_source_network.canonical.mlb import canonicalize_schedule\n\nsample = {\n    "dates": [{\n        "games": [{\n            "gamePk": 12345,\n            "gameDate": "2026-09-05T19:10:00Z",\n            "season": "2026",\n            "status": {"abstractGameState": "Live"},\n            "teams": {\n                "home": {"team": {"name": "Houston Astros"}, "score": 3},\n                "away": {"team": {"name": "Seattle Mariners"}, "score": 2},\n            },\n        }]\n    }]\n}\n\nrows = canonicalize_schedule(sample, "2026-09-05T20:00:00Z")\nassert len(rows) == 1\nx = rows[0]\nassert x.provider == "mlb_statsapi"\nassert x.identity.league == "MLB"\nassert x.identity.event_id.startswith("osn:sport:")\nassert x.home_score == 3\nassert x.away_score == 2\nassert x.execution_authority is False\nassert x.source_authority == "official_league"\nassert len(x.payload_sha256) == 64\nprint("[PASS] deterministic MLB canonicalization certified")\n\nprobe = """\nfrom datetime import date\nfrom qseries_v2.oracle_source_network.acquisition.mlb_live import acquire_date\n\nrows = acquire_date(str(date.today()), timeout=8.0)\nprint(f"[PHYSICAL] official_mlb_events={len(rows)}")\n\nassert isinstance(rows, tuple)\nfor row in rows:\n    assert row.provider == "mlb_statsapi"\n    assert row.source_authority == "official_league"\n    assert row.execution_authority is False\n    assert row.provider_event_id\n    assert row.identity.event_id.startswith("osn:sport:")\n    assert len(row.payload_sha256) == 64\n\nprint("[PASS] official MLB physical read completed")\n"""\n\ntry:\n    completed = subprocess.run(\n        [sys.executable, "-c", probe],\n        text=True,\n        capture_output=True,\n        timeout=15,\n    )\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("official MLB physical probe exceeded hard 15-second wall-clock gate")\n\nif completed.stdout:\n    print(completed.stdout.rstrip())\nif completed.stderr:\n    print(completed.stderr.rstrip())\n\nassert completed.returncode == 0, (\n    "official MLB physical probe failed with return code " + str(completed.returncode)\n)\n\nprint("[PASS] physical probe wall-clock bounded <=15 seconds")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-004 MLB official live acquisition certified")\n')

    print("[PASS] OSN-004 bounded physical rebuild installed")
    print("[PASS] hard physical wall-clock gate=15s")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
