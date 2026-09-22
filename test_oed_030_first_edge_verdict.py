
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_030_first_edge_verdict import build
s,p=build(Path.cwd())
assert p.exists() and s["tradable_edge_count"]==s["profitability_proven_count"]
assert s["verdict"] in {"FIRST_REPEATABLE_PROFITABLE_EDGE_CERTIFIED",
                        "BEHAVIORAL_SIGNAL_SURVIVED_BUT_NOT_YET_PROFITABLE_TRADABLE_EDGE",
                        "NO_EDGE_SURVIVED_STRICT_OUT_OF_SAMPLE_VALIDATION"}
print("[VERDICT_FILE]",p)
print("[OOS_RULES_TESTED]",s["oos_rules_tested"])
print("[RAW_SURVIVORS]",s["raw_survivors"])
print("[HOLM_BEHAVIOR_SURVIVORS]",s["holm_behavior_survivors"])
print("[REGIME_STABLE_SURVIVORS]",s["regime_stable_survivors"])
print("[PROFITABILITY_PROVEN]",s["profitability_proven_count"])
print("[TRADABLE_EDGE_COUNT]",s["tradable_edge_count"])
print("[VERDICT]",s["verdict"])
print("[NEXT_ACTION]",s["next_action"])
print("[VERDICT_HASH]",s["verdict_hash"])
print("[PASS] OED-026..OED-030 strict edge-validation slice complete")
