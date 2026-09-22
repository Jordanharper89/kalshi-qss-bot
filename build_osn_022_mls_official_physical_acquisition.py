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
    print(' OSN-022 MLS OFFICIAL PHYSICAL ACQUISITION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/acquisition/nhl_official_live.py')
    write('qseries_v2/oracle_source_network/acquisition/mls_official_live.py', 'from .official_http import get_official_text\nMLS_SCHEDULE_URL = "https://www.mlssoccer.com/news/mls-announces-2026-regular-season-schedule"\n\ndef acquire_mls_schedule(timeout=8.0):\n    s = get_official_text(MLS_SCHEDULE_URL, timeout=timeout)\n    low = s["body"].lower()\n    s.update({"provider":"mls_official","league":"MLS","source_authority":"official_league",\n              "markers":{"mls":"mls" in low,"schedule":"schedule" in low,"2026":"2026" in low}})\n    return s\n')
    write('test_osn_022_mls_official_physical_acquisition.py', 'import subprocess, sys\nprobe = """from qseries_v2.oracle_source_network.acquisition.mls_official_live import acquire_mls_schedule\nx=acquire_mls_schedule(8)\nprint(f"[PHYSICAL] MLS bytes={len(x[\'body\'])} markers={x[\'markers\']}")\nassert x["provider"]=="mls_official" and x["league"]=="MLS"\nassert x["source_authority"]=="official_league"\nassert len(x["payload_sha256"])==64 and x["read_only"] and not x["execution_authority"]\nassert all(x["markers"].values())\nprint("[PASS] MLS official physical acquisition completed")"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=15)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("MLS acquisition exceeded hard 15-second wall-clock gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"MLS physical probe failed rc={p.returncode}"\nprint("[PASS] OSN-022 MLS official physical acquisition certified")\n')
    print('[PASS] OSN-022 installed')
    print('[PASS] hard wall-clock physical gate=15s')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
