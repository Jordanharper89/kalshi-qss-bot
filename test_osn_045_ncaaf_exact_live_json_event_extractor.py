
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.mapping.ncaa_exact_json_event_extractor import extract_ncaa_events
_,payload=acquire_live_payload("NCAAF",8.0)
events=extract_ncaa_events(payload["body"],"NCAAF","ncaa_football_official","official_governing_body")
print(f"[PHYSICAL] NCAAF bytes={len(payload['body'].encode('utf-8'))} events={len(events)} unique={len({e.canonical_event_id for e in events})}")
for e in events[:5]:
    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start}")
assert len(events)>0, "NCAAF live application/json structure exists but exact extractor produced zero events"
assert len({e.canonical_event_id for e in events})==len(events)
print("[PASS] NCAAF exact live JSON extraction physically certified")
"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=25)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-045 exceeded hard 25-second gate")
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0, f"OSN-045 failed rc={p.returncode}"
print("[PASS] OSN-045 NCAAF exact live JSON event extractor certified")
