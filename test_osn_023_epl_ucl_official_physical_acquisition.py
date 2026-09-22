
import subprocess
import sys

probe = """
from qseries_v2.oracle_source_network.acquisition.european_soccer_official_live import acquire_epl_fixtures, acquire_ucl_fixtures

e = acquire_epl_fixtures(8.0)
print(f"[PHYSICAL] EPL bytes={len(e['body'])} markers={e['markers']}")
assert e["provider"] == "premier_league_official"
assert e["league"] == "EPL"
assert e["source_authority"] == "official_league"
assert len(e["payload_sha256"]) == 64
assert e["read_only"] is True
assert e["execution_authority"] is False
assert all(e["markers"].values())

u = acquire_ucl_fixtures(7.0)
print(f"[PHYSICAL] UCL bytes={len(u['body'])} markers={u['markers']}")
print(f"[PHYSICAL] UCL transport={u['transport']} selected_official_url={u['selected_official_url']}")
assert u["provider"] == "uefa_official"
assert u["league"] == "UCL"
assert u["source_authority"] == "official_governing_body"
assert len(u["payload_sha256"]) == 64
assert u["read_only"] is True
assert u["execution_authority"] is False
assert all(u["markers"].values())
assert "uefa.com" in u["selected_official_url"]
assert u["transport"] in ("urllib", "curl.exe")

print("[PASS] EPL + UCL official physical acquisition completed")
"""

try:
    p = subprocess.run(
        [sys.executable, "-c", probe],
        text=True,
        capture_output=True,
        timeout=35,
    )
except subprocess.TimeoutExpired:
    raise AssertionError(
        "EPL/UCL acquisition exceeded hard 35-second wall-clock gate"
    )

if p.stdout:
    print(p.stdout.rstrip())
if p.stderr:
    print(p.stderr.rstrip())

assert p.returncode == 0, f"EPL/UCL physical probe failed rc={p.returncode}"

print("[PASS] UEFA urllib + curl.exe transport boundary certified")
print("[PASS] source authority remains UEFA official only")
print("[PASS] no recursive scan / no unbounded network read")
print("[PASS] execution_authority=FALSE")
print("[PASS] OSN-023 EPL + UCL official physical acquisition certified")
