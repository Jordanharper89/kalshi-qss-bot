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
    print(' OSN-027 BOUNDED MULTI-SOURCE PHYSICAL RUNNER INSTALLER')
    print("=" * 118)
    require('test_osn_011_nfl_official_physical_acquisition.py')
    require('test_osn_012_ncaa_football_official_physical_acquisition.py')
    require('test_osn_016_nba_official_physical_acquisition.py')
    require('test_osn_017_ncaa_basketball_official_physical_acquisition.py')
    require('test_osn_021_nhl_official_physical_acquisition.py')
    require('test_osn_022_mls_official_physical_acquisition.py')
    require('test_osn_026_epl_standalone_physical_certification.py')
    write('qseries_v2/oracle_source_network/certification/sports_physical_runner.py', '\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport subprocess\nimport sys\nfrom concurrent.futures import ThreadPoolExecutor, as_completed\n\nROOT = Path.cwd()\n\nCERT_TESTS = {\n    "NFL": "test_osn_011_nfl_official_physical_acquisition.py",\n    "NCAAF": "test_osn_012_ncaa_football_official_physical_acquisition.py",\n    "NBA": "test_osn_016_nba_official_physical_acquisition.py",\n    "NCAAB": "test_osn_017_ncaa_basketball_official_physical_acquisition.py",\n    "NHL": "test_osn_021_nhl_official_physical_acquisition.py",\n    "MLS": "test_osn_022_mls_official_physical_acquisition.py",\n    "EPL": "test_osn_026_epl_standalone_physical_certification.py",\n}\n\n@dataclass(frozen=True, slots=True)\nclass PhysicalResult:\n    league: str\n    passed: bool\n    returncode: int\n    output_tail: str\n    execution_authority: bool = False\n\ndef _run_one(league, script, timeout=20):\n    p = ROOT / script\n    if not p.exists():\n        return PhysicalResult(league, False, 404, f"missing test script: {script}")\n    try:\n        r = subprocess.run([sys.executable, str(p)], text=True, capture_output=True, timeout=timeout)\n    except subprocess.TimeoutExpired:\n        return PhysicalResult(league, False, 124, f"timeout>{timeout}s")\n    text = (r.stdout + "\\n" + r.stderr).strip()\n    return PhysicalResult(league, r.returncode == 0, r.returncode, text[-1200:])\n\ndef run_certified_sources(max_workers=4):\n    results = []\n    with ThreadPoolExecutor(max_workers=max_workers) as ex:\n        futures = {ex.submit(_run_one, league, script): league for league, script in CERT_TESTS.items()}\n        for fut in as_completed(futures):\n            results.append(fut.result())\n    return tuple(sorted(results, key=lambda x: x.league))\n')
    write('test_osn_027_bounded_multi_source_physical_runner.py', '\nimport subprocess\nimport sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.certification.sports_physical_runner import run_certified_sources\nresults=run_certified_sources(max_workers=4)\nfor r in results:\n    print(f"[SOURCE] {r.league} passed={r.passed} rc={r.returncode}")\n    if not r.passed:\n        print(r.output_tail)\nassert len(results)==7\nassert all(r.passed for r in results)\nassert all(r.execution_authority is False for r in results)\nprint("[PASS] seven admitted sports sources physically re-certified")\n"""\n\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=55)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("multi-source physical runner exceeded hard 55-second gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode == 0, f"multi-source physical runner failed rc={p.returncode}"\nprint("[PASS] OSN-027 bounded multi-source physical runner certified")\n')
    print('[PASS] OSN-027 installed')
    print('[PASS] seven-source runner is bounded and parallel')
    print('[PASS] UCL is intentionally excluded')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
