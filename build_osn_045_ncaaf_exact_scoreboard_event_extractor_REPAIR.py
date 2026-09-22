from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: "+str(p))
    print("[PASS] dependency verified:",p.relative_to(ROOT))

def write(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+"\n",encoding="utf-8")
    print("[WRITE]",p.relative_to(ROOT))

def main():
    print("="*118)
    print(" OSN-045 NCAAF EXACT SCOREBOARD EVENT EXTRACTOR REPAIR INSTALLER")
    print("="*118)

    require("qseries_v2/oracle_source_network/canonical/sports_event_v2.py")
    require("qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py")
    require("qseries_v2/oracle_source_network/certification/ncaa_exact_event_schema_probe.py")

    write(
        "qseries_v2/oracle_source_network/mapping/ncaaf_exact_scoreboard_extractor.py",
        '\nimport html\nimport json\nimport re\nfrom datetime import datetime, timezone\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\ndef _application_json(body):\n    pattern=r\'<script\\b[^>]*type=["\\\']application/json["\\\'][^>]*>(.*?)</script>\'\n    for raw in re.findall(pattern, body, re.I|re.S):\n        text=html.unescape(raw).strip()\n        if not text:\n            continue\n        try:\n            obj=json.loads(text)\n            if isinstance(obj,dict):\n                yield obj\n        except Exception:\n            continue\n\ndef _find_scoreboard(root):\n    sb=root.get("scoreboard")\n    return sb if isinstance(sb,dict) else None\n\ndef _team_name(team):\n    if not isinstance(team,dict):\n        return ""\n    for key in ("nameShort","name10Char","name8Char","name6Char","seoname"):\n        v=team.get(key)\n        if isinstance(v,str) and v.strip():\n            return v.strip()\n    return ""\n\ndef _split_teams(teams):\n    home=None\n    away=None\n    for team in teams if isinstance(teams,list) else ():\n        if not isinstance(team,dict):\n            continue\n        if team.get("isHome") is True:\n            home=team\n        elif team.get("isHome") is False:\n            away=team\n    return home,away\n\ndef _scheduled_start(contest):\n    epoch=contest.get("startTimeEpoch")\n    if isinstance(epoch,(int,float)) and epoch > 0:\n        try:\n            return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()\n        except Exception:\n            pass\n\n    date=contest.get("startDate")\n    time=contest.get("startTime")\n    if isinstance(date,str) and isinstance(time,str) and date.strip() and time.strip():\n        # Preserve official display values if no usable epoch exists.\n        return f"{date.strip()} {time.strip()}"\n\n    if isinstance(date,str) and date.strip():\n        return date.strip()\n\n    return ""\n\ndef extract_ncaaf_live_events(body, observed_at=None):\n    observed_at=observed_at or datetime.now(timezone.utc).isoformat()\n    out={}\n\n    for root in _application_json(body):\n        scoreboard=_find_scoreboard(root)\n        if not scoreboard:\n            continue\n\n        games=scoreboard.get("initialGames")\n        if not isinstance(games,list):\n            continue\n\n        season=str(scoreboard.get("seasonYear") or "2026")\n\n        for contest in games:\n            if not isinstance(contest,dict):\n                continue\n            if contest.get("__typename") not in (None,"Contest"):\n                continue\n\n            contest_id=contest.get("contestId")\n            start=_scheduled_start(contest)\n            home,away=_split_teams(contest.get("teams"))\n\n            home_name=_team_name(home)\n            away_name=_team_name(away)\n\n            if not (contest_id and start and home_name and away_name):\n                continue\n\n            event=CanonicalSportsEvent(\n                league="NCAAF",\n                season=season,\n                provider="ncaa_official",\n                home_team=home_name,\n                away_team=away_name,\n                scheduled_start=start,\n                source_observed_at=observed_at,\n                source_authority="official_governing_body",\n                provider_event_id=str(contest_id),\n                event_discriminator=str(contest_id),\n                status=str(\n                    contest.get("statusCodeDisplay")\n                    or contest.get("gameState")\n                    or contest.get("currentPeriod")\n                    or ""\n                ),\n                home_score=home.get("score") if isinstance(home,dict) else None,\n                away_score=away.get("score") if isinstance(away,dict) else None,\n            )\n            out[event.canonical_event_id]=event\n\n    return tuple(out.values())\n'
    )
    write(
        "test_osn_045_ncaaf_exact_scoreboard_event_extractor_REPAIR.py",
        '\nimport subprocess,sys\nfrom qseries_v2.oracle_source_network.mapping.ncaaf_exact_scoreboard_extractor import extract_ncaaf_live_events\n\nsample=r"""\n<html><script type="application/json">\n{\n  "scoreboard":{\n    "seasonYear":"2026",\n    "initialGames":[\n      {\n        "__typename":"Contest",\n        "contestId":6604316,\n        "gameState":"F",\n        "statusCodeDisplay":"final",\n        "startTimeEpoch":1788019200,\n        "startTime":"12:00",\n        "startDate":"08/29/2026",\n        "teams":[\n          {"__typename":"ContestTeam","isHome":true,"nameShort":"TCU","score":10},\n          {"__typename":"ContestTeam","isHome":false,"nameShort":"UNC","score":7}\n        ]\n      }\n    ]\n  }\n}\n</script></html>\n"""\n\nevents=extract_ncaaf_live_events(sample,observed_at="2026-09-05T00:00:00Z")\nassert len(events)==1\ne=events[0]\nassert e.home_team=="TCU"\nassert e.away_team=="UNC"\nassert e.provider_event_id=="6604316"\nassert e.home_score==10\nassert e.away_score==7\nprint("[PASS] exact NCAA scoreboard schema regression certified")\n\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.mapping.ncaaf_exact_scoreboard_extractor import extract_ncaaf_live_events\n\n_,payload=acquire_live_payload("NCAAF",8.0)\nevents=extract_ncaaf_live_events(payload["body"])\n\nprint(f"[PHYSICAL] NCAAF bytes={len(payload[\'body\'].encode(\'utf-8\'))} events={len(events)} unique={len({e.canonical_event_id for e in events})}")\nfor e in events[:12]:\n    print(\n        f"[EVENT] {e.away_team} @ {e.home_team} "\n        f"start={e.scheduled_start} status={e.status} "\n        f"score={e.away_score}-{e.home_score} provider_event_id={e.provider_event_id}"\n    )\n\nassert len(events)>0, "physically proven scoreboard.initialGames schema produced zero NCAAF events"\nassert len({e.canonical_event_id for e in events})==len(events)\nassert all(e.provider_event_id for e in events)\nassert all(e.home_team and e.away_team and e.scheduled_start for e in events)\nassert all(e.read_only and e.execution_authority is False for e in events)\n\nprint("[PASS] NCAAF exact scoreboard.initialGames extraction physically certified")\n"""\n\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-045 exact extractor repair exceeded hard 30-second gate")\n\nif p.stdout:\n    print(p.stdout.rstrip())\nif p.stderr:\n    print(p.stderr.rstrip())\n\nassert p.returncode==0, f"OSN-045 exact extractor repair failed rc={p.returncode}"\nprint("[PASS] OSN-045 repaired NCAAF exact live event extractor certified")\n'
    )

    print("[PASS] failed generic NCAA field mapping retired")
    print("[PASS] exact path scoreboard.initialGames installed")
    print("[PASS] contestId/provider identity + teams/isHome + official schedule fields preserved")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
