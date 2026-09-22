
import subprocess,sys

# Deterministic ranking regression.
from qseries_v2.oracle_source_network.certification.ncaa_exact_event_schema_probe import inspect_ncaaf_event_schema

sample=r"""
<html><script type="application/json">
{"data":{"games":[{"contest_id":"123","start_date":"2026-09-05","home":{"name":"Alpha"},"away":{"name":"Beta"},"status":"scheduled"}]}}
</script></html>
"""
docs,rows=inspect_ncaaf_event_schema(sample)
assert docs==1
assert rows
print("[PASS] NCAA exact-schema ranking regression certified")

probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.certification.ncaa_exact_event_schema_probe import inspect_ncaaf_event_schema,print_schema

_,payload=acquire_live_payload("NCAAF",8.0)
docs,rows=inspect_ncaaf_event_schema(payload["body"])
print_schema(docs,rows)

assert len(payload["body"])>0
assert docs>0, "NCAAF application/json document disappeared"
assert rows, "NCAAF JSON exists but no ranked event-like object shapes were found"

print("[PASS] NCAAF exact live JSON object schema physically captured")
"""

try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-045 exact-schema repair exceeded hard 30-second gate")

if p.stdout:
    print(p.stdout.rstrip())
if p.stderr:
    print(p.stderr.rstrip())

assert p.returncode==0, f"OSN-045 exact-schema repair failed rc={p.returncode}"
print("[PASS] OSN-045 NCAAF exact live event-schema probe certified")
