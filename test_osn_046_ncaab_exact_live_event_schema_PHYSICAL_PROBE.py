
import subprocess,sys
from qseries_v2.oracle_source_network.certification.ncaab_exact_event_schema_probe import inspect_ncaab_event_schema

sample=r"""
<html><script type="application/json">
{"data":{"games":[{"contestId":"123","startDate":"2026-11-01","teams":[{"isHome":true,"nameShort":"Alpha"},{"isHome":false,"nameShort":"Beta"}]}]}}
</script></html>
"""
docs,rows=inspect_ncaab_event_schema(sample)
assert docs==1
assert rows
print("[PASS] NCAAB exact-schema ranking regression certified")

probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.certification.ncaab_exact_event_schema_probe import inspect_ncaab_event_schema,print_schema

_,payload=acquire_live_payload("NCAAB",8.0)
docs,rows=inspect_ncaab_event_schema(payload["body"])
print_schema(docs,rows)

assert len(payload["body"])>0
assert docs>0, "NCAAB application/json document disappeared"
assert rows, "NCAAB JSON exists but no ranked event-like object shapes were found"

print("[PASS] NCAAB exact live JSON object schema physically captured")
"""

try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-046 exact-schema probe exceeded hard 30-second gate")

if p.stdout:
    print(p.stdout.rstrip())
if p.stderr:
    print(p.stderr.rstrip())

assert p.returncode==0, f"OSN-046 exact-schema probe failed rc={p.returncode}"
print("[PASS] OSN-046 NCAAB exact live event-schema probe certified")
