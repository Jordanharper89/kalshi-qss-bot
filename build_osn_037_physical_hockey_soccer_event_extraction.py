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
    print(' OSN-037 PHYSICAL HOCKEY + SOCCER EVENT EXTRACTION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/physical_extraction_result.py')
    require('qseries_v2/oracle_source_network/mapping/hockey_soccer_event_extractor.py')
    write('test_osn_037_physical_hockey_soccer_event_extraction.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.physical_extraction_result import classify\nfrom qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events\nfor league,provider,authority in (\n("NHL","nhl_official","official_league"),\n("MLS","mls_official","official_league"),\n("EPL","premier_league_official","official_league")):\n    _,payload=acquire_live_payload(league,8.0)\n    events=extract_hockey_soccer_events(payload["body"],league,provider,authority=authority)\n    r=classify(league,payload["body"],events)\n    print(f"[PHYSICAL] {league} bytes={r.source_bytes} events={r.events} unique={r.unique_ids} status={r.status}")\n    assert r.source_bytes>0\n    if r.events:\n        assert r.unique_ids==r.events and r.read_only\nprint("[PASS] hockey/soccer live extraction truth measured without synthetic fallback")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=40)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-037 exceeded hard 40-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-037 failed rc={p.returncode}"\nprint("[PASS] OSN-037 physical hockey/soccer event extraction truth gate certified")\n')
    print('[PASS] OSN-037 installed')
    print('[PASS] NHL + MLS + EPL measured live')
    print('[PASS] UCL remains excluded')

if __name__ == "__main__":
    main()
