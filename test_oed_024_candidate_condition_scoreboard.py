
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_024_candidate_condition_scoreboard import build
s,p=build(Path.cwd()); assert s["candidate_groups"]>0 and s["ranking_is_discovery_only"]
assert s["multiple_testing_uncontrolled"] and not s["oos_validated"] and s["certified_edge_count"]==0
print("[CANDIDATE_GROUPS]",s["candidate_groups"]); print("[HASH]",s["scoreboard_hash"]); print("[TOP_RESEARCH_CANDIDATES]")
for x in s["scoreboard"][:30]: print(" ",x)
print("[PASS] apparent lift ranked but not promoted to edge")
print("[PASS] OED-024 candidate condition scoreboard certified")
