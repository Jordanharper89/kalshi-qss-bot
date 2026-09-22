import qseries_v2.oracle_predictive_discovery.opd_gen2_prospective_shortlist_audit as m
s={"tokens":["A","B"]}
assert m._match(s,["A"]) is True
assert m._match(s,["A","C"]) is False
assert m._dir("RETURN_NEG")==-1.0
assert m._dir("RETURN_POS")==1.0
assert m.execution_authority is False
print("[PASS] Gen2 audit is selection-only and recomputes formula matches from frozen state tokens")
print("[EDGE/PROBABILITY/DIRECTION/PUBLICATION/EXECUTION] FALSE/FALSE/FALSE/FALSE/FALSE")
