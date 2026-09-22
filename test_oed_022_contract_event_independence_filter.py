
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_022_contract_event_independence_filter import build
s,p=build(Path.cwd()); assert s["independent_rows"]>0 and s["independent_rows"]<=s["input_rows"]
assert s["contract_day_oos_not_yet_claimed"] and not s["edge_proven"]
print("[INPUT]",s["input_rows"]); print("[INDEPENDENT]",s["independent_rows"]); print("[REMOVED]",s["duplicates_removed"])
print("[HASH]",s["population_hash"]); print("[PASS] OED-022 event-independence filter certified")
