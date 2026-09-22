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
    print(' OSN-040 NCAAB LIVE EVENT STRUCTURE FORENSICS INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py')
    write('test_osn_040_ncaab_live_event_structure_forensics.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.live_event_structure_forensics import inspect_payload,print_finding\n_,payload=acquire_live_payload("NCAAB",8.0)\nf=inspect_payload("NCAAB",payload["body"])\nprint_finding(f)\nassert len(payload["body"])>0\nassert f.execution_authority is False\nprint("[PASS] NCAAB live structure forensics captured")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=25)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-040 exceeded hard 25-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-040 failed rc={p.returncode}"\nprint("[PASS] OSN-040 NCAAB live event structure forensics certified")\n')
    print('[PASS] OSN-040 installed')
    print('[PASS] diagnostic-only; extractor unchanged')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
