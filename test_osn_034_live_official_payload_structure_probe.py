
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload,profile_payload
from qseries_v2.oracle_source_network.certification.sports_source_truth import production_ready
leagues=tuple(x.league for x in production_ready())
assert leagues==("NFL","NCAAF","NBA","NCAAB","NHL","MLS","EPL")
for league in leagues:
    name,payload=acquire_live_payload(league,8.0)
    p=profile_payload(league,payload["body"])
    print(f"[STRUCTURE] {league} acquirer={name} bytes={p.bytes_read} scripts={p.script_count} app_json={p.application_json_scripts} parsed={p.json_parse_successes} next={p.next_data_present} ldjson={p.ld_json_present} tokens={p.event_tokens_present}")
    assert p.bytes_read>0
    assert p.execution_authority is False
print("[PASS] seven admitted live payloads physically profiled")
print("[PASS] no event structure was assumed or synthesized")
"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=70)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-034 exceeded hard 70-second gate")
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0, f"OSN-034 failed rc={p.returncode}"
print("[PASS] OSN-034 live official payload structure probe certified")
