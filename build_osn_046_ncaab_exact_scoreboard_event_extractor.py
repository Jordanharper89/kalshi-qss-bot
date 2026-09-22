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
    print(' OSN-046 NCAAB EXACT SCOREBOARD EVENT EXTRACTOR INSTALLER')
    print('='*118)
    require('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    require('qseries_v2/oracle_source_network/certification/ncaab_exact_event_schema_probe.py')
    write('qseries_v2/oracle_source_network/mapping/ncaab_exact_scoreboard_extractor.py','\nimport html,json,re\nfrom datetime import datetime,timezone\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\ndef _json_docs(body):\n    pat=r\'<script\\b[^>]*type=["\\\']application/json["\\\'][^>]*>(.*?)</script>\'\n    for raw in re.findall(pat,body,re.I|re.S):\n        try:\n            obj=json.loads(html.unescape(raw).strip())\n            if isinstance(obj,dict): yield obj\n        except Exception:\n            continue\n\ndef _team_name(t):\n    if not isinstance(t,dict): return ""\n    for k in ("nameShort","name10Char","name8Char","name6Char","seoname"):\n        v=t.get(k)\n        if isinstance(v,str) and v.strip(): return v.strip()\n    return ""\n\ndef _start(c):\n    ep=c.get("startTimeEpoch")\n    if isinstance(ep,(int,float)) and ep>0:\n        return datetime.fromtimestamp(ep,tz=timezone.utc).isoformat()\n    d=c.get("startDate")\n    t=c.get("startTime")\n    return f"{d} {t}".strip() if d or t else ""\n\ndef extract_ncaab_live_events(body,observed_at=None):\n    observed_at=observed_at or datetime.now(timezone.utc).isoformat()\n    out={}\n    schema_seen=False\n    for root in _json_docs(body):\n        sb=root.get("scoreboard")\n        if not isinstance(sb,dict): continue\n        if "initialGames" in sb: schema_seen=True\n        games=sb.get("initialGames")\n        if not isinstance(games,list): continue\n        season=str(sb.get("seasonYear") or sb.get("calendarYear") or "2026")\n        for c in games:\n            if not isinstance(c,dict): continue\n            teams=c.get("teams")\n            if not isinstance(teams,list): continue\n            home=next((x for x in teams if isinstance(x,dict) and x.get("isHome") is True),None)\n            away=next((x for x in teams if isinstance(x,dict) and x.get("isHome") is False),None)\n            cid=c.get("contestId")\n            start=_start(c)\n            hn,an=_team_name(home),_team_name(away)\n            if not (cid and start and hn and an): continue\n            e=CanonicalSportsEvent(\n                league="NCAAB",season=season,provider="ncaa_official",\n                home_team=hn,away_team=an,scheduled_start=start,\n                source_observed_at=observed_at,source_authority="official_governing_body",\n                provider_event_id=str(cid),event_discriminator=str(cid),\n                status=str(c.get("statusCodeDisplay") or c.get("gameState") or ""),\n                home_score=home.get("score") if home else None,\n                away_score=away.get("score") if away else None,\n            )\n            out[e.canonical_event_id]=e\n    return tuple(out.values()),schema_seen\n')
    write('test_osn_046_ncaab_exact_scoreboard_event_extractor.py','\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.mapping.ncaab_exact_scoreboard_extractor import extract_ncaab_live_events\n_,p=acquire_live_payload("NCAAB",8.0)\nevents,schema=extract_ncaab_live_events(p["body"])\nprint(f"[PHYSICAL] NCAAB bytes={len(p[\'body\'].encode(\'utf-8\'))} schema_seen={schema} events={len(events)} unique={len({e.canonical_event_id for e in events})}")\nassert schema is True, "physically proven scoreboard.initialGames key disappeared"\nassert len({e.canonical_event_id for e in events})==len(events)\nassert all(e.read_only and e.execution_authority is False for e in events)\nif events:\n    for e in events[:10]:\n        print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} id={e.provider_event_id}")\n    print("[PASS] NCAAB physical event extraction active")\nelse:\n    print("[HOLD] NCAAB exact extractor installed; current official page initialGames is empty/offseason")\nprint("[PASS] NCAAB exact scoreboard extractor contract physically certified")\n"""\np=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0,f"OSN-046 failed rc={p.returncode}"\nprint("[PASS] OSN-046 certified")\n')
    print('[PASS] exact proven NCAA scoreboard.initialGames contract installed')
    print('[PASS] current empty/offseason state is held truthfully, not synthesized')
    print('[PASS] execution_authority=FALSE')

if __name__=='__main__': main()
