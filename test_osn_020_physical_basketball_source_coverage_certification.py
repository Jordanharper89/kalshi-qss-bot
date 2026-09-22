
import subprocess, sys

probe = """
from qseries_v2.oracle_source_network.acquisition.nba_official_live import acquire_nba_games
from qseries_v2.oracle_source_network.acquisition.ncaa_basketball_official_live import acquire_ncaa_d1_mens_scoreboard
from qseries_v2.oracle_source_network.canonical.basketball import canonicalize_page_snapshot
from qseries_v2.oracle_source_network.health.basketball_source_health import evaluate
from qseries_v2.oracle_source_network.certification.basketball_physical_gate import certify

nba = acquire_nba_games(timeout=8.0)
ncaa = acquire_ncaa_d1_mens_scoreboard(timeout=8.0)

nba_obs = canonicalize_page_snapshot(nba)
ncaa_obs = canonicalize_page_snapshot(ncaa)
nba_health = evaluate(nba, max_age_seconds=120)
ncaa_health = evaluate(ncaa, max_age_seconds=120)

report = certify(nba_obs, ncaa_obs, nba_health, ncaa_health)
print(f"[PHYSICAL] NBA bytes={len(nba['body'])} detected_teams={len(nba.get('detected_teams',()))} markers={nba.get('markers')}")
print(f"[PHYSICAL] NCAAB bytes={len(ncaa['body'])} markers={ncaa.get('markers')}")
print(f"[CERT] {report}")
assert report["passed"] is True
assert report["physical_sources"] == 2
assert report["execution_authority"] is False
print("[PASS] physical basketball source coverage certified")
"""

try:
    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=25)
except subprocess.TimeoutExpired:
    raise AssertionError("basketball physical certification exceeded hard 25-second wall-clock gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode == 0, f"basketball physical certification failed rc={p.returncode}"
print("[PASS] OSN-020 NBA + NCAA basketball physical certification complete")
