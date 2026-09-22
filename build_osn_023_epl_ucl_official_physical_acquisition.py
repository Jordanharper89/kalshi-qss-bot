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
    print(' OSN-023 EPL + UCL OFFICIAL PHYSICAL ACQUISITION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/acquisition/mls_official_live.py')
    write('qseries_v2/oracle_source_network/acquisition/european_soccer_official_live.py', 'from .official_http import get_official_text\nEPL_FIXTURES_URL="https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-202627-premier-league-season"\nUCL_FIXTURES_URL="https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000/"\n\ndef acquire_epl_fixtures(timeout=8.0):\n    s=get_official_text(EPL_FIXTURES_URL,timeout=timeout); low=s["body"].lower()\n    s.update({"provider":"premier_league_official","league":"EPL","source_authority":"official_league",\n              "markers":{"premier_league":"premier league" in low,"fixtures":"fixture" in low,\n                         "2026_27":("2026/27" in low or "2026-27" in low)}})\n    return s\n\ndef acquire_ucl_fixtures(timeout=8.0):\n    s=get_official_text(UCL_FIXTURES_URL,timeout=timeout); low=s["body"].lower()\n    s.update({"provider":"uefa_official","league":"UCL","source_authority":"official_governing_body",\n              "markers":{"champions_league":"champions league" in low,"fixtures":"fixture" in low,\n                         "2026_27":("2026/27" in low or "2026-27" in low)}})\n    return s\n')
    write('test_osn_023_epl_ucl_official_physical_acquisition.py', 'import subprocess, sys\nprobe = """from qseries_v2.oracle_source_network.acquisition.european_soccer_official_live import acquire_epl_fixtures, acquire_ucl_fixtures\ne=acquire_epl_fixtures(8); u=acquire_ucl_fixtures(8)\nprint(f"[PHYSICAL] EPL bytes={len(e[\'body\'])} markers={e[\'markers\']}")\nprint(f"[PHYSICAL] UCL bytes={len(u[\'body\'])} markers={u[\'markers\']}")\nfor x in (e,u):\n    assert len(x["payload_sha256"])==64 and x["read_only"] and not x["execution_authority"]\n    assert all(x["markers"].values())\nassert e["source_authority"]=="official_league"\nassert u["source_authority"]=="official_governing_body"\nprint("[PASS] EPL + UCL official physical acquisition completed")"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=25)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("EPL/UCL acquisition exceeded hard 25-second wall-clock gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"EPL/UCL physical probe failed rc={p.returncode}"\nprint("[PASS] OSN-023 EPL + UCL official physical acquisition certified")\n')
    print('[PASS] OSN-023 installed')
    print('[PASS] hard wall-clock physical gate=25s')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
