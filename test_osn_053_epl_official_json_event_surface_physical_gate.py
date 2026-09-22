
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.acquisition.epl_official_fpl_event_surface import extract_epl_fixtures
braw,fraw,events=extract_epl_fixtures(timeout=8.0)
print(f"[PHYSICAL] EPL bootstrap_bytes={len(braw)} fixture_bytes={len(fraw)} events={len(events)} unique={len({e.canonical_event_id for e in events})}")
for e in events[:12]:
    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} status={e.status} id={e.provider_event_id}")
assert len(braw)>0 and len(fraw)>0
assert len(events)>0,"official Premier League/FPL fixture JSON returned zero canonical events"
assert len({e.canonical_event_id for e in events})==len(events)
assert all(e.read_only and e.execution_authority is False for e in events)
print("[PASS] EPL official Premier League JSON fixture extraction physically certified")
"""
p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0,f"OSN-053 failed rc={p.returncode}"
print("[PASS] OSN-053 EPL production event surface certified")
