
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.mapping.nfl_live_script_state_extractor import extract_nfl_live_events
_,payload=acquire_live_payload("NFL",8.0)
events=extract_nfl_live_events(payload["body"])
print(f"[PHYSICAL] NFL bytes={len(payload['body'].encode('utf-8'))} events={len(events)} unique={len({e.canonical_event_id for e in events})}")
for e in events[:5]:
    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} id={e.canonical_event_id}")
assert len(events)>0, "NFL live page contained game-bearing state but exact extractor produced zero events"
assert len({e.canonical_event_id for e in events})==len(events)
assert all(e.read_only and e.execution_authority is False for e in events)
print("[PASS] NFL exact live script-state extraction physically certified")
"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=35)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-044 exceeded hard 35-second gate")
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0, f"OSN-044 failed rc={p.returncode}"
print("[PASS] OSN-044 NFL exact live script-state extractor certified")
