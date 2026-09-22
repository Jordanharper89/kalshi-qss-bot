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
    print(' OSN-021 NHL OFFICIAL PHYSICAL ACQUISITION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/providers/hockey_soccer_official.py')
    require('qseries_v2/oracle_source_network/acquisition/official_http.py')
    write('qseries_v2/oracle_source_network/acquisition/nhl_official_live.py', 'from .official_http import get_official_text\nNHL_SCHEDULE_URL = "https://www.nhl.com/schedule"\n\ndef acquire_nhl_schedule(timeout=8.0):\n    s = get_official_text(NHL_SCHEDULE_URL, timeout=timeout)\n    low = s["body"].lower()\n    s.update({"provider":"nhl_official","league":"NHL","source_authority":"official_league",\n              "markers":{"nhl":"nhl" in low,"schedule":"schedule" in low}})\n    return s\n')
    write('test_osn_021_nhl_official_physical_acquisition.py', 'import subprocess, sys\nprobe = """from qseries_v2.oracle_source_network.acquisition.nhl_official_live import acquire_nhl_schedule\nx=acquire_nhl_schedule(8)\nprint(f"[PHYSICAL] NHL bytes={len(x[\'body\'])} markers={x[\'markers\']}")\nassert x["provider"]=="nhl_official" and x["league"]=="NHL"\nassert x["source_authority"]=="official_league"\nassert len(x["payload_sha256"])==64 and x["read_only"] and not x["execution_authority"]\nassert all(x["markers"].values())\nprint("[PASS] NHL official physical acquisition completed")"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=15)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("NHL acquisition exceeded hard 15-second wall-clock gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"NHL physical probe failed rc={p.returncode}"\nprint("[PASS] OSN-021 NHL official physical acquisition certified")\n')
    print('[PASS] OSN-021 installed')
    print('[PASS] hard wall-clock physical gate=15s')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
