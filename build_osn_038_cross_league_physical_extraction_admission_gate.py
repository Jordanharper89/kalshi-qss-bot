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
    print(' OSN-038 CROSS-LEAGUE PHYSICAL EXTRACTION ADMISSION GATE INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py')
    require('qseries_v2/oracle_source_network/certification/physical_extraction_result.py')
    require('qseries_v2/oracle_source_network/mapping/football_event_extractor.py')
    require('qseries_v2/oracle_source_network/mapping/basketball_event_extractor.py')
    require('qseries_v2/oracle_source_network/mapping/hockey_soccer_event_extractor.py')
    write('qseries_v2/oracle_source_network/certification/physical_extraction_admission.py', '\nfrom dataclasses import dataclass\n@dataclass(frozen=True, slots=True)\nclass ExtractionAdmission:\n    league: str\n    status: str\n    events: int\n    admitted: bool\n    reason: str\n    execution_authority: bool = False\n\ndef decide(result):\n    if result.status=="EXTRACTING" and result.events>0 and result.unique_ids==result.events and result.read_only:\n        return ExtractionAdmission(result.league,result.status,result.events,True,"live canonical events physically extracted")\n    return ExtractionAdmission(result.league,result.status,result.events,False,"not admitted until live official payload yields canonical events")\n')
    write('test_osn_038_cross_league_physical_extraction_admission_gate.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.physical_extraction_result import classify\nfrom qseries_v2.oracle_source_network.certification.physical_extraction_admission import decide\nfrom qseries_v2.oracle_source_network.mapping.football_event_extractor import extract_football_events\nfrom qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events\nfrom qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events\nspecs=(\n("NFL","nfl_official","official_league","football"),\n("NCAAF","ncaa_football_official","official_governing_body","football"),\n("NBA","nba_official","official_league","basketball"),\n("NCAAB","ncaa_basketball_official","official_governing_body","basketball"),\n("NHL","nhl_official","official_league","hockey_soccer"),\n("MLS","mls_official","official_league","hockey_soccer"),\n("EPL","premier_league_official","official_league","hockey_soccer"))\nadmissions=[]\nfor league,provider,authority,family in specs:\n    _,payload=acquire_live_payload(league,8.0)\n    if family=="football":\n        events=extract_football_events(payload["body"],league,provider,authority=authority)\n    elif family=="basketball":\n        events=extract_basketball_events(payload["body"],league,provider,authority=authority)\n    else:\n        events=extract_hockey_soccer_events(payload["body"],league,provider,authority=authority)\n    r=classify(league,payload["body"],events)\n    a=decide(r); admissions.append(a)\n    print(f"[ADMISSION] {league} status={a.status} events={a.events} admitted={a.admitted}")\nassert len(admissions)==7\nassert all(a.execution_authority is False for a in admissions)\nprint("[CERT] physically_extracted_admitted=",tuple(a.league for a in admissions if a.admitted))\nprint("[CERT] held_for_structure_or_current_event_gap=",tuple(a.league for a in admissions if not a.admitted))\nprint("[PASS] OSN-038 reported physical extraction admission truth")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=75)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-038 exceeded hard 75-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-038 failed rc={p.returncode}"\nprint("[PASS] OSN-038 cross-league physical extraction admission gate certified")\n')
    print('[PASS] OSN-038 installed')
    print('[PASS] only real live event producers can be admitted')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
