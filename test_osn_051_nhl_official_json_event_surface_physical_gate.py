
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.acquisition.nhl_official_json_event_surface import URI,extract_nhl_opening_schedule
raw,events=extract_nhl_opening_schedule(timeout=8.0)
print(f"[PHYSICAL] NHL uri={URI} bytes={len(raw)} events={len(events)} unique={len({e.canonical_event_id for e in events})}")
for e in events[:10]:
    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} status={e.status} id={e.provider_event_id}")
assert len(raw)>0
assert len(events)>0,"NHL-owned JSON schedule surface returned no canonical events"
assert len({e.canonical_event_id for e in events})==len(events)
assert all(e.read_only and e.execution_authority is False for e in events)
print("[PASS] NHL official JSON event surface physically certified")
"""
p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0,f"OSN-051 failed rc={p.returncode}"
print("[PASS] OSN-051 NHL production event surface certified")
