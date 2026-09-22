
import subprocess, sys

probe = """
from qseries_v2.oracle_source_network.acquisition.nba_official_live import acquire_nba_games
x = acquire_nba_games(timeout=8.0)
print(f"[PHYSICAL] provider={x['provider']} bytes={len(x['body'])} detected_teams={len(x['detected_teams'])} markers={x['markers']}")
assert x["provider"] == "nba_official"
assert x["league"] == "NBA"
assert x["source_authority"] == "official_league"
assert len(x["payload_sha256"]) == 64
assert x["read_only"] is True
assert x["execution_authority"] is False
assert sum(bool(v) for v in x["markers"].values()) >= 2
assert len(x["detected_teams"]) >= 2
print("[PASS] NBA official physical acquisition completed")
"""

try:
    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=15)
except subprocess.TimeoutExpired:
    raise AssertionError("NBA official acquisition exceeded hard 15-second wall-clock gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode == 0, f"NBA physical probe failed rc={p.returncode}"
print("[PASS] OSN-016 NBA official physical acquisition certified")
