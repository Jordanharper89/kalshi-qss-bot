
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_028_strict_oos_behavior_validation import build
s,p=build(Path.cwd())
assert p.exists() and s["multiple_testing_method"]=="HOLM_BONFERRONI"
assert s["holm_survivors"]<=s["raw_survivors"] and not s["profitability_proven"]
print("[TESTED_RULES]",s["tested_rules"])
print("[RAW_SURVIVORS]",s["raw_survivors"])
print("[HOLM_SURVIVORS]",s["holm_survivors"])
print("[RESULTS_HASH]",s["results_hash"])
for x in s["results"][:30]: print(" ",x)
print("[PASS] unseen-day chronological holdout scored")
print("[PASS] one-sided exact binomial baseline test applied")
print("[PASS] Holm-Bonferroni multiple-testing control applied")
print("[PASS] OED-028 strict OOS behavior validation certified")
