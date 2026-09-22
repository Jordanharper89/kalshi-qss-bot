
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload
from qseries_v2.oracle_source_network.mapping.ncaab_exact_scoreboard_extractor import extract_ncaab_live_events
_,p=acquire_live_payload("NCAAB",8.0)
events,schema=extract_ncaab_live_events(p["body"])
print(f"[PHYSICAL] NCAAB bytes={len(p['body'].encode('utf-8'))} schema_seen={schema} events={len(events)} unique={len({e.canonical_event_id for e in events})}")
assert schema is True, "physically proven scoreboard.initialGames key disappeared"
assert len({e.canonical_event_id for e in events})==len(events)
assert all(e.read_only and e.execution_authority is False for e in events)
if events:
    for e in events[:10]:
        print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} id={e.provider_event_id}")
    print("[PASS] NCAAB physical event extraction active")
else:
    print("[HOLD] NCAAB exact extractor installed; current official page initialGames is empty/offseason")
print("[PASS] NCAAB exact scoreboard extractor contract physically certified")
"""
p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0,f"OSN-046 failed rc={p.returncode}"
print("[PASS] OSN-046 certified")
