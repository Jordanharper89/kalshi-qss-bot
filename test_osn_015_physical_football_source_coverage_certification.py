
import subprocess, sys

probe = """
from qseries_v2.oracle_source_network.acquisition.nfl_official_live import acquire_nfl_scores
from qseries_v2.oracle_source_network.acquisition.ncaa_football_official_live import acquire_ncaa_fbs_scoreboard
from qseries_v2.oracle_source_network.canonical.football import canonicalize_page_snapshot
from qseries_v2.oracle_source_network.health.football_source_health import evaluate
from qseries_v2.oracle_source_network.certification.football_physical_gate import certify

nfl = acquire_nfl_scores(timeout=8.0)
ncaa = acquire_ncaa_fbs_scoreboard(timeout=8.0)

nfl_obs = canonicalize_page_snapshot(nfl)
ncaa_obs = canonicalize_page_snapshot(ncaa)
nfl_health = evaluate(nfl, max_age_seconds=120)
ncaa_health = evaluate(ncaa, max_age_seconds=120)

report = certify(nfl_obs, ncaa_obs, nfl_health, ncaa_health)
print(f"[PHYSICAL] NFL bytes={len(nfl['body'])} detected_teams={len(nfl.get('detected_teams',()))}")
print(f"[PHYSICAL] NCAAF bytes={len(ncaa['body'])} markers={ncaa.get('markers')}")
print(f"[CERT] {report}")
assert report["passed"] is True
assert report["physical_sources"] == 2
assert report["execution_authority"] is False
print("[PASS] physical football source coverage certified")
"""

try:
    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=25)
except subprocess.TimeoutExpired:
    raise AssertionError("football physical certification exceeded hard 25-second wall-clock gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode == 0, f"football physical certification failed rc={p.returncode}"
print("[PASS] OSN-015 NFL + NCAA football physical certification complete")
