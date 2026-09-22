
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.certification.physical_extraction_result import classify
from qseries_v2.oracle_source_network.mapping.hockey_soccer_event_extractor import extract_hockey_soccer_events
for league,provider,authority in (
("NHL","nhl_official","official_league"),
("MLS","mls_official","official_league"),
("EPL","premier_league_official","official_league")):
    _,payload=acquire_live_payload(league,8.0)
    events=extract_hockey_soccer_events(payload["body"],league,provider,authority=authority)
    r=classify(league,payload["body"],events)
    print(f"[PHYSICAL] {league} bytes={r.source_bytes} events={r.events} unique={r.unique_ids} status={r.status}")
    assert r.source_bytes>0
    if r.events:
        assert r.unique_ids==r.events and r.read_only
print("[PASS] hockey/soccer live extraction truth measured without synthetic fallback")
"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=40)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-037 exceeded hard 40-second gate")
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0, f"OSN-037 failed rc={p.returncode}"
print("[PASS] OSN-037 physical hockey/soccer event extraction truth gate certified")
