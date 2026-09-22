
import subprocess, sys

probe = """
from qseries_v2.oracle_source_network.acquisition.ncaa_basketball_official_live import acquire_ncaa_d1_mens_scoreboard
x = acquire_ncaa_d1_mens_scoreboard(timeout=8.0)
print(f"[PHYSICAL] provider={x['provider']} bytes={len(x['body'])} markers={x['markers']}")
assert x["provider"] == "ncaa_official"
assert x["league"] == "NCAAB"
assert x["source_authority"] == "official_governing_body"
assert len(x["payload_sha256"]) == 64
assert x["read_only"] is True
assert x["execution_authority"] is False
assert x["markers"]["basketball"] is True
assert x["markers"]["ncaa"] is True
assert sum(bool(v) for v in x["markers"].values()) >= 3
print("[PASS] NCAA basketball official physical acquisition completed")
"""

try:
    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=15)
except subprocess.TimeoutExpired:
    raise AssertionError("NCAA basketball acquisition exceeded hard 15-second wall-clock gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode == 0, f"NCAA basketball physical probe failed rc={p.returncode}"
print("[PASS] OSN-017 NCAA basketball official physical acquisition certified")
