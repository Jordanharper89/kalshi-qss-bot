
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path.cwd()

CERT_TESTS = {
    "NFL": "test_osn_011_nfl_official_physical_acquisition.py",
    "NCAAF": "test_osn_012_ncaa_football_official_physical_acquisition.py",
    "NBA": "test_osn_016_nba_official_physical_acquisition.py",
    "NCAAB": "test_osn_017_ncaa_basketball_official_physical_acquisition.py",
    "NHL": "test_osn_021_nhl_official_physical_acquisition.py",
    "MLS": "test_osn_022_mls_official_physical_acquisition.py",
    "EPL": "test_osn_026_epl_standalone_physical_certification.py",
}

@dataclass(frozen=True, slots=True)
class PhysicalResult:
    league: str
    passed: bool
    returncode: int
    output_tail: str
    execution_authority: bool = False

def _run_one(league, script, timeout=20):
    p = ROOT / script
    if not p.exists():
        return PhysicalResult(league, False, 404, f"missing test script: {script}")
    try:
        r = subprocess.run([sys.executable, str(p)], text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return PhysicalResult(league, False, 124, f"timeout>{timeout}s")
    text = (r.stdout + "\n" + r.stderr).strip()
    return PhysicalResult(league, r.returncode == 0, r.returncode, text[-1200:])

def run_certified_sources(max_workers=4):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_run_one, league, script): league for league, script in CERT_TESTS.items()}
        for fut in as_completed(futures):
            results.append(fut.result())
    return tuple(sorted(results, key=lambda x: x.league))
