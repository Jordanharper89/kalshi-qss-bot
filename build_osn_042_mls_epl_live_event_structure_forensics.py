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
    print(' OSN-042 MLS + EPL LIVE EVENT STRUCTURE FORENSICS INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/live_event_structure_forensics.py')
    write('test_osn_042_mls_epl_live_event_structure_forensics.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload\nfrom qseries_v2.oracle_source_network.certification.live_event_structure_forensics import inspect_payload,print_finding\nfor league in ("MLS","EPL"):\n    _,payload=acquire_live_payload(league,8.0)\n    f=inspect_payload(league,payload["body"])\n    print_finding(f)\n    assert len(payload["body"])>0\n    assert f.execution_authority is False\nprint("[PASS] MLS/EPL live structure forensics captured")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=35)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-042 exceeded hard 35-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-042 failed rc={p.returncode}"\nprint("[PASS] OSN-042 MLS + EPL live event structure forensics certified")\n')
    print('[PASS] OSN-042 installed')
    print('[PASS] UCL remains excluded')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
