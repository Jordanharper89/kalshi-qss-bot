
import subprocess, sys

probe = """
from qseries_v2.oracle_source_network.acquisition.nfl_official_live import acquire_nfl_scores
x = acquire_nfl_scores(timeout=8.0)
print(f"[PHYSICAL] provider={x['provider']} bytes={len(x['body'])} detected_teams={len(x['detected_teams'])}")
assert x["provider"] == "nfl_official"
assert x["league"] == "NFL"
assert x["source_authority"] == "official_league"
assert len(x["payload_sha256"]) == 64
assert x["read_only"] is True
assert x["execution_authority"] is False
assert len(x["detected_teams"]) >= 2
print("[PASS] NFL official physical acquisition completed")
"""

try:
    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=15)
except subprocess.TimeoutExpired:
    raise AssertionError("NFL official acquisition exceeded hard 15-second wall-clock gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode == 0, f"NFL physical probe failed rc={p.returncode}"
print("[PASS] OSN-011 NFL official physical acquisition certified")
