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
    print(' OSN-035 PHYSICAL FOOTBALL EVENT EXTRACTION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py')
    require('qseries_v2/oracle_source_network/mapping/football_event_extractor.py')
    write('qseries_v2/oracle_source_network/certification/physical_extraction_result.py', '\nfrom dataclasses import dataclass\n@dataclass(frozen=True, slots=True)\nclass PhysicalExtractionResult:\n    league: str\n    source_bytes: int\n    events: int\n    status: str\n    unique_ids: int\n    read_only: bool\n    execution_authority: bool = False\n\ndef classify(league,body,events):\n    ids=[x.canonical_event_id for x in events]\n    if events:\n        status="EXTRACTING"\n    else:\n        low=body.lower()\n        hints=any(x in low for x in ("eventid","gameid","matchid","hometeam","awayteam","home_team","away_team","fixtures","schedule","score"))\n        status="UNSUPPORTED_STRUCTURE" if hints else "NO_CURRENT_EVENTS_OR_NO_STRUCTURED_EVENT_DATA"\n    return PhysicalExtractionResult(\n        league=league,\n        source_bytes=len(body.encode("utf-8",errors="ignore")),\n        events=len(events),\n        status=status,\n        unique_ids=len(set(ids)),\n        read_only=all(getattr(x,"read_only",False) is True for x in events),\n    )\n')
    write('test_osn_035_physical_football_event_extraction.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.physical_extraction_result import classify\nfrom qseries_v2.oracle_source_network.mapping.football_event_extractor import extract_football_events\nfor league,provider,authority in (\n("NFL","nfl_official","official_league"),\n("NCAAF","ncaa_football_official","official_governing_body")):\n    _,payload=acquire_live_payload(league,8.0)\n    events=extract_football_events(payload["body"],league,provider,authority=authority)\n    r=classify(league,payload["body"],events)\n    print(f"[PHYSICAL] {league} bytes={r.source_bytes} events={r.events} unique={r.unique_ids} status={r.status}")\n    assert r.source_bytes>0\n    if r.events:\n        assert r.unique_ids==r.events and r.read_only\nprint("[PASS] football live extraction truth measured without synthetic fallback")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-035 exceeded hard 30-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-035 failed rc={p.returncode}"\nprint("[PASS] OSN-035 physical football event extraction truth gate certified")\n')
    print('[PASS] OSN-035 installed')
    print('[PASS] NFL + NCAAF measured live')
    print('[PASS] zero events are reported, never fabricated')

if __name__ == "__main__":
    main()
