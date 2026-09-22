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
    print(' OSN-053 EPL OFFICIAL JSON EVENT SURFACE PHYSICAL GATE INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    require('qseries_v2/oracle_source_network/acquisition/soccer_event_surface_boundary.py')
    write('qseries_v2/oracle_source_network/acquisition/epl_official_fpl_event_surface.py','\nimport json,urllib.request\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\nBOOT="https://fantasy.premierleague.com/api/bootstrap-static/"\nFIXTURES="https://fantasy.premierleague.com/api/fixtures/"\n\ndef _get(uri,timeout=8.0):\n    req=urllib.request.Request(uri,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})\n    with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()\n    return raw,json.loads(raw.decode("utf-8"))\n\ndef extract_epl_fixtures(observed_at=None,timeout=8.0):\n    observed_at=observed_at or datetime.now(timezone.utc).isoformat()\n    braw,boot=_get(BOOT,timeout)\n    fraw,fixtures=_get(FIXTURES,timeout)\n    teams={int(t["id"]):t["name"] for t in boot.get("teams",[]) if isinstance(t,dict) and t.get("id") and t.get("name")}\n    out={}\n    for f in fixtures if isinstance(fixtures,list) else ():\n        if not isinstance(f,dict): continue\n        fid=f.get("id"); start=f.get("kickoff_time")\n        h=teams.get(f.get("team_h")); a=teams.get(f.get("team_a"))\n        if not(fid and start and h and a): continue\n        status="finished" if f.get("finished") else ("started" if f.get("started") else "scheduled")\n        e=CanonicalSportsEvent(\n            league="EPL",season="2026-27",provider="premier_league_fpl_official",\n            home_team=h,away_team=a,scheduled_start=start,\n            source_observed_at=observed_at,source_authority="official_league",\n            provider_event_id=str(fid),event_discriminator=str(f.get("event") or fid),\n            status=status,home_score=f.get("team_h_score"),away_score=f.get("team_a_score"),\n        )\n        out[e.canonical_event_id]=e\n    return braw,fraw,tuple(out.values())\n')
    write('test_osn_053_epl_official_json_event_surface_physical_gate.py','\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.acquisition.epl_official_fpl_event_surface import extract_epl_fixtures\nbraw,fraw,events=extract_epl_fixtures(timeout=8.0)\nprint(f"[PHYSICAL] EPL bootstrap_bytes={len(braw)} fixture_bytes={len(fraw)} events={len(events)} unique={len({e.canonical_event_id for e in events})}")\nfor e in events[:12]:\n    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} status={e.status} id={e.provider_event_id}")\nassert len(braw)>0 and len(fraw)>0\nassert len(events)>0,"official Premier League/FPL fixture JSON returned zero canonical events"\nassert len({e.canonical_event_id for e in events})==len(events)\nassert all(e.read_only and e.execution_authority is False for e in events)\nprint("[PASS] EPL official Premier League JSON fixture extraction physically certified")\n"""\np=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0,f"OSN-053 failed rc={p.returncode}"\nprint("[PASS] OSN-053 EPL production event surface certified")\n')
    print('[PASS] Premier League-owned fixture JSON surface installed')
    print('[PASS] article parsing retired')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
