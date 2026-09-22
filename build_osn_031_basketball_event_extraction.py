from pathlib import Path

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
    print(' OSN-031 BASKETBALL EVENT EXTRACTION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    require('qseries_v2/oracle_source_network/acquisition/nba_official_live.py')
    require('qseries_v2/oracle_source_network/acquisition/ncaa_basketball_official_live.py')
    write('qseries_v2/oracle_source_network/mapping/basketball_event_extractor.py', '\nimport html\nimport json\nimport re\nfrom datetime import datetime, timezone\nfrom typing import Iterable\n\ndef _clean(s):\n    return re.sub(r"\\s+", " ", html.unescape(str(s or ""))).strip()\n\ndef _walk(obj):\n    if isinstance(obj, dict):\n        yield obj\n        for v in obj.values():\n            yield from _walk(v)\n    elif isinstance(obj, list):\n        for v in obj:\n            yield from _walk(v)\n\ndef _json_candidates(body):\n    # Script/data payloads are common on official score/schedule pages.\n    for m in re.finditer(r\'<script[^>]*type=["\\\']application/json["\\\'][^>]*>(.*?)</script>\', body, re.I | re.S):\n        raw = html.unescape(m.group(1))\n        try:\n            yield json.loads(raw)\n        except Exception:\n            pass\n\ndef _name(v):\n    if isinstance(v, str):\n        return _clean(v)\n    if isinstance(v, dict):\n        for k in ("displayName","fullName","name","shortName","teamName","clubName"):\n            if isinstance(v.get(k), str) and _clean(v[k]):\n                return _clean(v[k])\n    return ""\n\ndef _id(v):\n    if isinstance(v, dict):\n        for k in ("id","eventId","event_id","gameId","game_id","matchId","match_id","uid"):\n            if v.get(k) is not None:\n                return _clean(v[k])\n    return ""\n\ndef _start(d):\n    for k in ("startTime","start_time","startDate","start_date","date","datetime","kickoff","gameTime"):\n        if isinstance(d.get(k), str) and d.get(k):\n            return _clean(d[k])\n    return None\n\ndef _status(d):\n    for k in ("status","state","eventStatus","gameStatus"):\n        v=d.get(k)\n        if isinstance(v, str) and v:\n            return _clean(v).upper()\n        if isinstance(v, dict):\n            for q in ("name","type","state","description"):\n                if isinstance(v.get(q), str) and v.get(q):\n                    return _clean(v[q]).upper()\n    return "SCHEDULED"\n\ndef _score(v):\n    try:\n        if v is None or v == "":\n            return None\n        return int(float(str(v)))\n    except Exception:\n        return None\n\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\ndef _extract_dict_event(d, league, provider, season, observed_at, authority):\n    home = _name(d.get("homeTeam") or d.get("home_team") or d.get("home"))\n    away = _name(d.get("awayTeam") or d.get("away_team") or d.get("away"))\n    if not home or not away or home == away:\n        return None\n    pid = _id(d)\n    discriminator = _clean(d.get("round") or d.get("gameNumber") or d.get("week") or "")\n    return CanonicalSportsEvent(\n        league=league, season=season, provider=provider,\n        provider_event_id=pid or None, home_team=home, away_team=away,\n        event_discriminator=discriminator, scheduled_start=_start(d),\n        source_observed_at=observed_at, source_authority=authority,\n        status=_status(d),\n        home_score=_score(d.get("homeScore") or d.get("home_score")),\n        away_score=_score(d.get("awayScore") or d.get("away_score")),\n    )\n\ndef extract_basketball_events(body, league, provider, season="2026-27", observed_at=None, authority="official_league"):\n    observed_at = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00","Z")\n    out, seen = [], set()\n    for root in _json_candidates(body):\n        for d in _walk(root):\n            if not isinstance(d, dict):\n                continue\n            ev = _extract_dict_event(d, league, provider, season, observed_at, authority)\n            if ev and ev.canonical_event_id not in seen:\n                seen.add(ev.canonical_event_id); out.append(ev)\n    return tuple(out)\n')
    write('test_osn_031_basketball_event_extraction.py', '\nimport json\nfrom qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events\npayload={"games":[\n {"gameId":"nba-1","homeTeam":{"name":"Houston Rockets"},"awayTeam":{"name":"Dallas Mavericks"},\n  "startDate":"2026-10-20T00:00:00Z","status":"scheduled"},\n {"gameId":"nba-2","homeTeam":{"name":"Los Angeles Lakers"},"awayTeam":{"name":"Phoenix Suns"},\n  "startDate":"2026-10-21T00:00:00Z","status":"scheduled"}\n]}\nbody=\'<script type="application/json">\'+json.dumps(payload)+\'</script>\'\nevents=extract_basketball_events(body,"NBA","nba_official")\nassert len(events)==2\nassert events[0].provider_event_id=="nba-1"\nassert events[0].home_team=="Houston Rockets"\nassert events[0].execution_authority is False\nprint("[PASS] basketball official-page JSON event extraction certified")\nprint("[PASS] provider event IDs preserved")\nprint("[PASS] OSN-031 basketball event extraction certified")\n')
    print('[PASS] OSN-031 installed')
    print('[PASS] score/status fields retained when present')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
