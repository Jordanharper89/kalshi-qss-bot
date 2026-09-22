
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_027_locked_discovery_rulebook import build
s,p=build(Path.cwd())
assert p.exists() and s["rule_locked_before_test"] and not s["test_data_consulted"]
assert s["rule_count"]>=0 and not s["edge_proven"]
print("[RULES]",s["rule_count"])
print("[RULEBOOK_HASH]",s["rulebook_hash"])
for x in sorted(s["rules"],key=lambda z:(-z["train_raw_lift"],-z["train_n"]))[:30]: print(" ",x)
print("[PASS] prediction rule determined from discovery/train rows only")
print("[PASS] test outcomes hidden from rule selection")
print("[PASS] OED-027 locked discovery rulebook certified")
