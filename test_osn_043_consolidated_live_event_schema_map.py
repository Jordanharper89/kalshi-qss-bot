
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.certification.live_event_structure_forensics import inspect_payload
from qseries_v2.oracle_source_network.certification.live_schema_map import map_result
leagues=("NFL","NCAAF","NBA","NCAAB","NHL","MLS","EPL")
rows=[]
for league in leagues:
    _,payload=acquire_live_payload(league,8.0)
    finding=inspect_payload(league,payload["body"])
    row=map_result(league,finding,already_extracting=(league=="NBA"))
    rows.append(row)
    print(f"[SCHEMA_MAP] {league} candidates={row.structured_candidates} json_paths={row.has_json_paths} token_contexts={row.has_token_contexts} action={row.action}")
assert len(rows)==7
assert [r for r in rows if r.league=="NBA"][0].action=="PRESERVE_WORKING_EXTRACTOR"
assert all(r.execution_authority is False for r in rows)
print("[PASS] live source-specific extraction work map produced")
print("[PASS] NBA retained as positive control")
"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=75)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-043 exceeded hard 75-second gate")
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0, f"OSN-043 failed rc={p.returncode}"
print("[PASS] OSN-043 consolidated live schema map certified")
