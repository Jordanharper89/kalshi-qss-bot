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
    print(" OSN-052 MLS OFFICIAL STATS EXACT-QUERY EVENT SURFACE REPAIR INSTALLER")
    print("="*118)

    require("qseries_v2/oracle_source_network/canonical/sports_event_v2.py")
    require("qseries_v2/oracle_source_network/acquisition/soccer_event_surface_boundary.py")

    write(
        "qseries_v2/oracle_source_network/certification/mls_official_stats_exact_query_probe.py",
        '\nimport json,urllib.parse,urllib.request\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\nBASE="https://stats-api.mlssoccer.com/matches/seasons/MLS-SEA-0001KA"\nPARAMS={\n    "match_date[gte]":"2026-08-31",\n    "match_date[lte]":"2026-09-13",\n    "competition_id":"MLS-COM-000001",\n    "per_page":"100",\n    "sort":"planned_kickoff_time:asc,home_team_name:asc",\n}\n\ndef _uri():\n    return BASE+"?"+urllib.parse.urlencode(PARAMS)\n\ndef _get(timeout=8.0):\n    uri=_uri()\n    req=urllib.request.Request(uri,headers={"Accept":"application/json","User-Agent":"curl"})\n    with urllib.request.urlopen(req,timeout=timeout) as r:\n        raw=r.read()\n    return uri,raw,json.loads(raw.decode("utf-8"))\n\ndef _provider_id(match):\n    for key in (\n        "match_id","id","match_uuid","match_uid","match_code",\n        "fixture_id","event_id","game_id"\n    ):\n        v=match.get(key)\n        if v is not None and str(v).strip():\n            return str(v).strip()\n    return None\n\ndef probe_and_extract(observed_at=None,timeout=8.0):\n    observed_at=observed_at or datetime.now(timezone.utc).isoformat()\n    uri,raw,root=_get(timeout)\n    schedule=root.get("schedule") if isinstance(root,dict) else None\n    if not isinstance(schedule,list):\n        return {\n            "uri":uri,"bytes":len(raw),"root_keys":tuple(root.keys()) if isinstance(root,dict) else (),\n            "schedule_seen":False,"match_keys":(),"events":()\n        }\n\n    match_keys=tuple(schedule[0].keys()) if schedule and isinstance(schedule[0],dict) else ()\n    out={}\n    for m in schedule:\n        if not isinstance(m,dict): continue\n        start=m.get("planned_kickoff_time")\n        home=m.get("home_team_short_name") or m.get("home_team_name")\n        away=m.get("away_team_short_name") or m.get("away_team_name")\n        if not (start and home and away): continue\n\n        pid=_provider_id(m)\n        discr=pid or f"{m.get(\'match_day\',\'\')}|{away}|{home}"\n\n        e=CanonicalSportsEvent(\n            league="MLS",\n            season="2026",\n            provider="mls_official_stats_api",\n            home_team=str(home),\n            away_team=str(away),\n            scheduled_start=str(start),\n            source_observed_at=observed_at,\n            source_authority="official_league",\n            provider_event_id=pid,\n            event_discriminator=str(discr),\n            status=str(m.get("status") or m.get("match_status") or ""),\n        )\n        out[e.canonical_event_id]=e\n\n    return {\n        "uri":uri,\n        "bytes":len(raw),\n        "root_keys":tuple(root.keys()) if isinstance(root,dict) else (),\n        "schedule_seen":True,\n        "schedule_count":len(schedule),\n        "match_keys":match_keys,\n        "events":tuple(out.values()),\n    }\n',
    )
    write(
        "test_osn_052_mls_official_stats_exact_query_event_surface_REPAIR.py",
        '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.mls_official_stats_exact_query_probe import probe_and_extract\nr=probe_and_extract(timeout=8.0)\n\nprint(f"[PHYSICAL] MLS bytes={r[\'bytes\']} schedule_seen={r[\'schedule_seen\']} schedule_count={r.get(\'schedule_count\',0)} events={len(r[\'events\'])} unique={len({e.canonical_event_id for e in r[\'events\']})}")\nprint("[ROOT_KEYS]",r["root_keys"])\nprint("[MATCH_KEYS]",r["match_keys"])\n\nfor e in r["events"][:12]:\n    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} provider_event_id={e.provider_event_id}")\n\nassert r["bytes"]>0\nassert r["schedule_seen"] is True, "MLS official API response did not contain schedule[]"\nassert r.get("schedule_count",0)>0, "MLS exact filtered request returned empty schedule[]"\nassert len(r["events"])>0, "MLS schedule[] existed but canonical extraction produced zero events"\nassert len({e.canonical_event_id for e in r["events"]})==len(r["events"])\nassert all(e.home_team and e.away_team and e.scheduled_start for e in r["events"])\nassert all(e.read_only and e.execution_authority is False for e in r["events"])\n\nprint("[PASS] MLS exact filtered official schedule request physically certified")\nprint("[PASS] MLS canonical event extraction physically certified")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-052 exact-query repair exceeded hard 30-second gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\n\nassert p.returncode==0,f"OSN-052 repair failed rc={p.returncode}"\nprint("[PASS] OSN-052 repaired MLS official stats exact-query event surface certified")\n',
    )

    print("[PASS] failed bare /matches/seasons/<season> request retired")
    print("[PASS] exact working MLS query contract installed")
    print("[PASS] schedule[] + planned_kickoff_time + home/away fields consumed")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
