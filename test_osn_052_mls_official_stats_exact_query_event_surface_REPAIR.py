
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.mls_official_stats_exact_query_probe import probe_and_extract
r=probe_and_extract(timeout=8.0)

print(f"[PHYSICAL] MLS bytes={r['bytes']} schedule_seen={r['schedule_seen']} schedule_count={r.get('schedule_count',0)} events={len(r['events'])} unique={len({e.canonical_event_id for e in r['events']})}")
print("[ROOT_KEYS]",r["root_keys"])
print("[MATCH_KEYS]",r["match_keys"])

for e in r["events"][:12]:
    print(f"[EVENT] {e.away_team} @ {e.home_team} start={e.scheduled_start} provider_event_id={e.provider_event_id}")

assert r["bytes"]>0
assert r["schedule_seen"] is True, "MLS official API response did not contain schedule[]"
assert r.get("schedule_count",0)>0, "MLS exact filtered request returned empty schedule[]"
assert len(r["events"])>0, "MLS schedule[] existed but canonical extraction produced zero events"
assert len({e.canonical_event_id for e in r["events"]})==len(r["events"])
assert all(e.home_team and e.away_team and e.scheduled_start for e in r["events"])
assert all(e.read_only and e.execution_authority is False for e in r["events"])

print("[PASS] MLS exact filtered official schedule request physically certified")
print("[PASS] MLS canonical event extraction physically certified")
"""
try:
    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)
except subprocess.TimeoutExpired:
    raise AssertionError("OSN-052 exact-query repair exceeded hard 30-second gate")

if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())

assert p.returncode==0,f"OSN-052 repair failed rc={p.returncode}"
print("[PASS] OSN-052 repaired MLS official stats exact-query event surface certified")
