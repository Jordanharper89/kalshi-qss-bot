
import subprocess,sys

# Deterministic walker regression first.
from qseries_v2.oracle_source_network.certification.live_event_structure_forensics import _walk
sample={
    "root":{
        "gameId":"abc",
        "homeTeam":{"name":"A"},
        "awayTeam":{"name":"B"},
        "startTime":"2026-09-10T00:00:00Z",
    }
}
rows=_walk(sample)
assert rows, "walker failed to detect event-bearing keys"
print("[PASS] forensic walker generator-scope defect repaired")

probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.certification.live_event_structure_forensics import inspect_payload,print_finding

for league in ("NFL","NCAAF"):
    _,payload=acquire_live_payload(league,8.0)
    f=inspect_payload(league,payload["body"])
    print_finding(f)
    assert len(payload["body"])>0
    assert f.execution_authority is False

print("[PASS] football live structure forensics captured")
"""

try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=35)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-039 repair physical gate exceeded hard 35-second limit")

if p.stdout:
    print(p.stdout.rstrip())
if p.stderr:
    print(p.stderr.rstrip())

assert p.returncode==0, f"OSN-039 repaired forensic gate failed rc={p.returncode}"

print("[PASS] OSN-039 repaired football live event structure forensics certified")
