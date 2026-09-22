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
    print(' OSN-026 EPL STANDALONE PHYSICAL CERTIFICATION INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/acquisition/european_soccer_official_live.py')
    write('test_osn_026_epl_standalone_physical_certification.py', '\nimport subprocess\nimport sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.acquisition.european_soccer_official_live import acquire_epl_fixtures\nx=acquire_epl_fixtures(8.0)\nprint(f"[PHYSICAL] EPL bytes={len(x[\'body\'])} markers={x[\'markers\']}")\nassert x["provider"]=="premier_league_official"\nassert x["league"]=="EPL"\nassert x["source_authority"]=="official_league"\nassert len(x["payload_sha256"])==64\nassert x["read_only"] is True\nassert x["execution_authority"] is False\nassert all(x["markers"].values())\nprint("[PASS] EPL standalone official physical acquisition certified")\n"""\n\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=15)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("EPL standalone certification exceeded hard 15-second gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode == 0, f"EPL standalone physical certification failed rc={p.returncode}"\nprint("[PASS] OSN-026 EPL standalone certification complete")\n')
    print('[PASS] OSN-026 installed')
    print('[PASS] hard wall-clock physical gate=15s')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
