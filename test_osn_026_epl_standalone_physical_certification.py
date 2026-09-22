
import subprocess
import sys

probe = """
from qseries_v2.oracle_source_network.acquisition.european_soccer_official_live import acquire_epl_fixtures
x=acquire_epl_fixtures(8.0)
print(f"[PHYSICAL] EPL bytes={len(x['body'])} markers={x['markers']}")
assert x["provider"]=="premier_league_official"
assert x["league"]=="EPL"
assert x["source_authority"]=="official_league"
assert len(x["payload_sha256"])==64
assert x["read_only"] is True
assert x["execution_authority"] is False
assert all(x["markers"].values())
print("[PASS] EPL standalone official physical acquisition certified")
"""

try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=15)
except subprocess.TimeoutExpired:
    raise AssertionError("EPL standalone certification exceeded hard 15-second gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode == 0, f"EPL standalone physical certification failed rc={p.returncode}"
print("[PASS] OSN-026 EPL standalone certification complete")
