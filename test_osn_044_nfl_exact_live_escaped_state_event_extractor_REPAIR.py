
import re, subprocess, sys
from qseries_v2.oracle_source_network.mapping.nfl_live_escaped_state_extractor import extract_nfl_live_events

# Deterministic regression matching the exact escaped state shape physically observed.
sample=(
    r'\"gameTime\":\"2026-09-11T00:35:00Z\",'
    r'\"homeTeam\":{\"abbreviation\":\"LAR\"},'
    r'\"linkName\":\"SF @ LAR\",'
    r'\"awayTeam\":{\"abbreviation\":\"SF\"},'
    r'\"abbreviationScreenReaderElementId\":\"sr-element-score-strip-10404500\"'
)
events=extract_nfl_live_events(sample, observed_at="2026-09-05T00:00:00Z")
assert events, "escaped-state deterministic regression produced zero events"
assert any(e.home_team=="LAR" and e.away_team=="SF" for e in events)
print("[PASS] escaped NFL state regression certified")

probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.mapping.nfl_live_escaped_state_extractor import extract_nfl_live_events

_,payload=acquire_live_payload("NFL",8.0)
events=extract_nfl_live_events(payload["body"])

print(f"[PHYSICAL] NFL bytes={len(payload['body'].encode('utf-8'))} events={len(events)} unique={len({e.canonical_event_id for e in events})}")
for e in events[:12]:
    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} provider_event_id={e.provider_event_id}")

assert len(events)>0, "NFL escaped live state was present but repaired extractor still produced zero events"
assert len({e.canonical_event_id for e in events})==len(events)
assert all(e.read_only and e.execution_authority is False for e in events)
assert all(e.home_team and e.away_team and e.scheduled_start for e in events)

print("[PASS] NFL escaped live script-state extraction physically certified")
"""

try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=35)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-044 escaped-state repair exceeded hard 35-second gate")

if p.stdout:
    print(p.stdout.rstrip())
if p.stderr:
    print(p.stderr.rstrip())

assert p.returncode==0, f"OSN-044 escaped-state repair failed rc={p.returncode}"
print("[PASS] OSN-044 repaired NFL exact live escaped-state extractor certified")
