
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_009_crypto_condition_raw_state_sequence_range_repair import build

s,p=build(Path.cwd())
assert p.exists()
assert s["row_count"]>0
assert s["source_count"]>0
assert s["global_observation_type_sort_used"] is False
assert s["read_only"] is True
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False

print("[FILE]",p)
print("[SEQUENCE_WINDOW]",s["sequence_window"])
print("[ROWS]",s["row_count"])
print("[SOURCES]",s["source_count"])
print("[QUERY_MODE]",s["query_mode"])
print("[GLOBAL_OBSERVATION_TYPE_SORT_USED]",s["global_observation_type_sort_used"])
print("[HASH]",s["hash"])
print("[TOP_SOURCES]")
for k,v in list(s["source_counts"].items())[:30]:
    print(" ",v,k)
print("[PASS] unbounded observation_type ORDER BY query retired")
print("[PASS] crypto raw conditions recovered through indexed sequence boundary")
print("[PASS] raw condition state remains feature-side only")
print("[PASS] OPD-009 crypto-condition raw-state SEQUENCE RANGE REPAIR certified")
