
import subprocess,sys
probe=r"""
from qseries_v2.oracle_source_network.certification.mls_official_stats_event_surface_probe import probe_surface
r=probe_surface(timeout=8.0)
print(f"[PHYSICAL] MLS season_bytes={r['season_bytes']} season_id={r['season_id']} match_bytes={r['match_bytes']} uri={r['matches_uri']}")
for i,(path,keys,scalars) in enumerate(r["sample_paths"],1):
    print(f"[MLS_CANDIDATE {i:02d}] path={path}")
    print("  keys=",keys)
    if scalars: print("  scalars=",scalars)
assert r["season_bytes"]>0
assert r["season_id"],"MLS-owned seasons API did not expose a 2026 season id"
assert r["match_bytes"]>0,"MLS-owned 2026 season match endpoint returned no payload"
assert r["sample_paths"],"MLS match payload returned but no event-like object shapes were found"
print("[PASS] MLS-owned 2026 production match surface physically proven")
print("[HOLD] MLS canonical extraction remains closed until exact printed match schema is mapped")
"""
p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=30)
if p.stdout: print(p.stdout.rstrip())
if p.stderr: print(p.stderr.rstrip())
assert p.returncode==0,f"OSN-052 failed rc={p.returncode}"
print("[PASS] OSN-052 MLS official stats event-surface probe certified")
