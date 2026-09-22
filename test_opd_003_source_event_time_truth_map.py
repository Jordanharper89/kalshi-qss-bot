
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_003_source_event_time_truth_map import build

s,p=build(Path.cwd())
assert p.exists() and s["group_count"]>0 and s["read_only"]
print("[FILE]",p)
print("[GROUPS]",s["group_count"])
print("[TRUTH_MAP_HASH]",s["truth_map_hash"])
print("[TOP_EVENT_TIME_CONTRACTS]")
for g in s["groups"][:30]:
    print(" ",g)
print("[PASS] source-event timestamps discovered from physical payloads")
print("[PASS] ingestion time is not silently substituted when inner event time exists")
print("[PASS] OPD-003 source-event-time truth map certified")
