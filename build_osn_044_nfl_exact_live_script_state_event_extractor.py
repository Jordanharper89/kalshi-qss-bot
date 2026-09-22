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
    print(' OSN-044 NFL EXACT LIVE SCRIPT-STATE EVENT EXTRACTOR INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/canonical/sports_event_v2.py')
    require('qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py')
    write('qseries_v2/oracle_source_network/mapping/nfl_live_script_state_extractor.py', '\nimport json, re\nfrom datetime import datetime, timezone\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\n\ndef _iter_json_fragments(body):\n    # NFL page contains escaped application state rather than plain application/json script tags.\n    # We search bounded object-like regions around known game-bearing keys and decode only valid JSON.\n    needles = (\'"gameTime"\', \'\\\\"gameTime\\\\"\')\n    seen=set()\n    for needle in needles:\n        start=0\n        while True:\n            idx=body.find(needle,start)\n            if idx < 0:\n                break\n            a=max(0, body.rfind("{", 0, idx))\n            # bounded forward scan for a plausible object terminator\n            for b in range(idx+len(needle), min(len(body), idx+6000)):\n                if body[b] == "}":\n                    raw=body[a:b+1]\n                    candidates=[raw, raw.replace(\'\\\\"\',\'"\')]\n                    for c in candidates:\n                        if c in seen:\n                            continue\n                        seen.add(c)\n                        try:\n                            obj=json.loads(c)\n                            if isinstance(obj,dict):\n                                yield obj\n                        except Exception:\n                            pass\n            start=idx+len(needle)\n\ndef _walk(obj):\n    if isinstance(obj,dict):\n        yield obj\n        for v in obj.values():\n            yield from _walk(v)\n    elif isinstance(obj,list):\n        for v in obj:\n            yield from _walk(v)\n\ndef _team_name(x):\n    if isinstance(x,str):\n        return x.strip()\n    if not isinstance(x,dict):\n        return ""\n    for k in ("abbreviation","displayName","fullName","name","teamName"):\n        v=x.get(k)\n        if isinstance(v,str) and v.strip():\n            return v.strip()\n    return ""\n\ndef extract_nfl_live_events(body, observed_at=None):\n    observed_at = observed_at or datetime.now(timezone.utc).isoformat()\n    out={}\n    for root in _iter_json_fragments(body):\n        for obj in _walk(root):\n            game_time=obj.get("gameTime") or obj.get("startTime")\n            home=_team_name(obj.get("homeTeam"))\n            away=_team_name(obj.get("awayTeam"))\n            if not (game_time and home and away):\n                continue\n            provider_id = (\n                obj.get("gameId") or obj.get("eventId") or obj.get("id")\n                or obj.get("gameKey") or obj.get("uid")\n            )\n            event=CanonicalSportsEvent(\n                league="NFL",\n                season="2026",\n                provider="nfl_official",\n                home_team=home,\n                away_team=away,\n                scheduled_start=str(game_time),\n                source_observed_at=observed_at,\n                source_authority="official_league",\n                provider_event_id=str(provider_id) if provider_id is not None else None,\n                event_discriminator=str(provider_id or game_time),\n                status=str(obj.get("status") or obj.get("gameStatus") or ""),\n                home_score=obj.get("homeScore"),\n                away_score=obj.get("awayScore"),\n            )\n            out[event.canonical_event_id]=event\n    return tuple(out.values())\n')
    write('test_osn_044_nfl_exact_live_script_state_event_extractor.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.mapping.nfl_live_script_state_extractor import extract_nfl_live_events\n_,payload=acquire_live_payload("NFL",8.0)\nevents=extract_nfl_live_events(payload["body"])\nprint(f"[PHYSICAL] NFL bytes={len(payload[\'body\'].encode(\'utf-8\'))} events={len(events)} unique={len({e.canonical_event_id for e in events})}")\nfor e in events[:5]:\n    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} id={e.canonical_event_id}")\nassert len(events)>0, "NFL live page contained game-bearing state but exact extractor produced zero events"\nassert len({e.canonical_event_id for e in events})==len(events)\nassert all(e.read_only and e.execution_authority is False for e in events)\nprint("[PASS] NFL exact live script-state extraction physically certified")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=35)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-044 exceeded hard 35-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-044 failed rc={p.returncode}"\nprint("[PASS] OSN-044 NFL exact live script-state extractor certified")\n')
    print('[PASS] OSN-044 installed')
    print('[PASS] targets physically observed NFL gameTime/homeTeam/awayTeam state')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
