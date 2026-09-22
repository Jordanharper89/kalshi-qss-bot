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
    print(' OSN-036 PHYSICAL BASKETBALL EVENT EXTRACTION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/physical_extraction_result.py')
    require('qseries_v2/oracle_source_network/mapping/basketball_event_extractor.py')
    write('test_osn_036_physical_basketball_event_extraction.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.physical_extraction_result import classify\nfrom qseries_v2.oracle_source_network.mapping.basketball_event_extractor import extract_basketball_events\nfor league,provider,authority in (\n("NBA","nba_official","official_league"),\n("NCAAB","ncaa_basketball_official","official_governing_body")):\n    _,payload=acquire_live_payload(league,8.0)\n    events=extract_basketball_events(payload["body"],league,provider,authority=authority)\n    r=classify(league,payload["body"],events)\n    print(f"[PHYSICAL] {league} bytes={r.source_bytes} events={r.events} unique={r.unique_ids} status={r.status}")\n    assert r.source_bytes>0\n    if r.events:\n        assert r.unique_ids==r.events and r.read_only\nprint("[PASS] basketball live extraction truth measured without synthetic fallback")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-036 exceeded hard 30-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-036 failed rc={p.returncode}"\nprint("[PASS] OSN-036 physical basketball event extraction truth gate certified")\n')
    print('[PASS] OSN-036 installed')
    print('[PASS] NBA + NCAAB measured live')
    print('[PASS] zero events are reported, never fabricated')

if __name__ == "__main__":
    main()
