
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_023_family_behavior_baseline import build
s,p=build(Path.cwd()); assert s["group_count"]>0 and s["baseline_is_descriptive"] and not s["candidate_beats_baseline"]
print("[GROUPS]",s["group_count"]); print("[HASH]",s["baseline_hash"])
for x in sorted(s["groups"],key=lambda z:z["sample_size"],reverse=True)[:25]: print(" ",x)
print("[PASS] no anomaly is allowed to call itself edge without beating family baseline")
print("[PASS] OED-023 family behavior baseline certified")
