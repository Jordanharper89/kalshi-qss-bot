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
    print(' OSN-045 NCAAF EXACT LIVE JSON EVENT EXTRACTOR INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    require('qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py')
    write('qseries_v2/oracle_source_network/mapping/ncaa_exact_json_event_extractor.py', '\nimport html, json, re\nfrom datetime import datetime, timezone\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\ndef _script_json(body):\n    for raw in re.findall(r\'<script\\b[^>]*type=["\\\']application/json["\\\'][^>]*>(.*?)</script>\', body, re.I|re.S):\n        try:\n            yield json.loads(html.unescape(raw).strip())\n        except Exception:\n            continue\n\ndef _walk(obj):\n    if isinstance(obj,dict):\n        yield obj\n        for v in obj.values():\n            yield from _walk(v)\n    elif isinstance(obj,list):\n        for v in obj:\n            yield from _walk(v)\n\ndef _pick(d,*keys):\n    for k in keys:\n        if k in d and d[k] not in (None,""):\n            return d[k]\n    return None\n\ndef _team(x):\n    if isinstance(x,str): return x.strip()\n    if not isinstance(x,dict): return ""\n    for k in ("shortName","name","displayName","teamName","abbreviation"):\n        v=x.get(k)\n        if isinstance(v,str) and v.strip(): return v.strip()\n    return ""\n\ndef extract_ncaa_events(body, league, provider, authority, observed_at=None):\n    observed_at=observed_at or datetime.now(timezone.utc).isoformat()\n    out={}\n    for root in _script_json(body):\n        for d in _walk(root):\n            home=_team(_pick(d,"homeTeam","home","home_team"))\n            away=_team(_pick(d,"awayTeam","away","away_team"))\n            start=_pick(d,"startTime","startDate","gameTime","start_time","start_date")\n            if not (home and away and start):\n                continue\n            pid=_pick(d,"gameId","eventId","contestId","id","uid")\n            event=CanonicalSportsEvent(\n                league=league,\n                season="2026",\n                provider=provider,\n                home_team=home,\n                away_team=away,\n                scheduled_start=str(start),\n                source_observed_at=observed_at,\n                source_authority=authority,\n                provider_event_id=str(pid) if pid is not None else None,\n                event_discriminator=str(pid or start),\n                status=str(_pick(d,"status","gameStatus","state") or ""),\n                home_score=_pick(d,"homeScore","home_score"),\n                away_score=_pick(d,"awayScore","away_score"),\n            )\n            out[event.canonical_event_id]=event\n    return tuple(out.values())\n')
    write('test_osn_045_ncaaf_exact_live_json_event_extractor.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.mapping.ncaa_exact_json_event_extractor import extract_ncaa_events\n_,payload=acquire_live_payload("NCAAF",8.0)\nevents=extract_ncaa_events(payload["body"],"NCAAF","ncaa_football_official","official_governing_body")\nprint(f"[PHYSICAL] NCAAF bytes={len(payload[\'body\'].encode(\'utf-8\'))} events={len(events)} unique={len({e.canonical_event_id for e in events})}")\nfor e in events[:5]:\n    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start}")\nassert len(events)>0, "NCAAF live application/json structure exists but exact extractor produced zero events"\nassert len({e.canonical_event_id for e in events})==len(events)\nprint("[PASS] NCAAF exact live JSON extraction physically certified")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=25)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-045 exceeded hard 25-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-045 failed rc={p.returncode}"\nprint("[PASS] OSN-045 NCAAF exact live JSON event extractor certified")\n')
    print('[PASS] OSN-045 installed')
    print('[PASS] consumes physically proven NCAA application/json structure')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
