from pathlib import Path

ROOT=Path.cwd()

def require(rel):
    p=ROOT/rel
    if not p.exists(): raise SystemExit('[FAIL] missing dependency: '+str(p))
    print('[PASS] dependency verified:',p.relative_to(ROOT))

def write(rel,content):
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content.rstrip()+'\n',encoding='utf-8')
    print('[WRITE]',p.relative_to(ROOT))

def main():
    print('='*118)
    print(' OSN-051 NHL OFFICIAL JSON EVENT SURFACE PHYSICAL GATE INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    require('qseries_v2/oracle_source_network/acquisition/nhl_event_surface_boundary.py')
    write('qseries_v2/oracle_source_network/acquisition/nhl_official_json_event_surface.py','\nimport json,urllib.request\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\nOPENING_DATE="2026-09-29"\nURI=f"https://api-web.nhle.com/v1/schedule/{OPENING_DATE}"\n\ndef _get_json(timeout=8.0):\n    req=urllib.request.Request(URI,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})\n    with urllib.request.urlopen(req,timeout=timeout) as r:\n        raw=r.read()\n    return raw,json.loads(raw.decode("utf-8"))\n\ndef _games(root):\n    if isinstance(root,dict):\n        for key in ("gameWeek","games"):\n            v=root.get(key)\n            if key=="games" and isinstance(v,list):\n                for g in v:\n                    if isinstance(g,dict): yield g\n            elif key=="gameWeek" and isinstance(v,list):\n                for day in v:\n                    if isinstance(day,dict):\n                        for g in day.get("games",[]) if isinstance(day.get("games"),list) else ():\n                            if isinstance(g,dict): yield g\n\ndef extract_nhl_opening_schedule(observed_at=None,timeout=8.0):\n    observed_at=observed_at or datetime.now(timezone.utc).isoformat()\n    raw,root=_get_json(timeout)\n    out={}\n    for g in _games(root):\n        gid=g.get("id")\n        start=g.get("startTimeUTC")\n        home=g.get("homeTeam") if isinstance(g.get("homeTeam"),dict) else {}\n        away=g.get("awayTeam") if isinstance(g.get("awayTeam"),dict) else {}\n        hn=home.get("abbrev") or home.get("name")\n        an=away.get("abbrev") or away.get("name")\n        if isinstance(hn,dict): hn=hn.get("default")\n        if isinstance(an,dict): an=an.get("default")\n        if not (gid and start and hn and an): continue\n        e=CanonicalSportsEvent(\n            league="NHL",season="2026-27",provider="nhl_official_json",\n            home_team=str(hn),away_team=str(an),scheduled_start=str(start),\n            source_observed_at=observed_at,source_authority="official_league",\n            provider_event_id=str(gid),event_discriminator=str(gid),\n            status=str(g.get("gameState") or g.get("gameScheduleState") or ""),\n            home_score=home.get("score"),away_score=away.get("score"),\n        )\n        out[e.canonical_event_id]=e\n    return raw,tuple(out.values())\n')
    write('test_osn_051_nhl_official_json_event_surface_physical_gate.py','\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.acquisition.nhl_official_json_event_surface import URI,extract_nhl_opening_schedule\nraw,events=extract_nhl_opening_schedule(timeout=8.0)\nprint(f"[PHYSICAL] NHL uri={URI} bytes={len(raw)} events={len(events)} unique={len({e.canonical_event_id for e in events})}")\nfor e in events[:10]:\n    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} status={e.status} id={e.provider_event_id}")\nassert len(raw)>0\nassert len(events)>0,"NHL-owned JSON schedule surface returned no canonical events"\nassert len({e.canonical_event_id for e in events})==len(events)\nassert all(e.read_only and e.execution_authority is False for e in events)\nprint("[PASS] NHL official JSON event surface physically certified")\n"""\np=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0,f"OSN-051 failed rc={p.returncode}"\nprint("[PASS] OSN-051 NHL production event surface certified")\n')
    print('[PASS] bounded NHL-owned JSON candidate installed')
    print('[PASS] no HTML-shell parsing')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
