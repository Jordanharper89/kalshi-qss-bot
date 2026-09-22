
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.certification.live_event_structure_forensics import inspect_payload,print_finding
_,payload=acquire_live_payload("NHL",8.0)
f=inspect_payload("NHL",payload["body"])
print_finding(f)
assert len(payload["body"])>0
assert f.execution_authority is False
print("[PASS] NHL live structure forensics captured")
"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=25)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-041 exceeded hard 25-second gate")
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0, f"OSN-041 failed rc={p.returncode}"
print("[PASS] OSN-041 NHL live event structure forensics certified")
