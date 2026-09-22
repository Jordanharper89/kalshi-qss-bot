import qseries_v2.oracle_predictive_discovery.opd_existing_prospective_edge_status_now as m
assert m._direction("RETURN_POS")=="UP"
assert m._direction("DOWN_5C")=="DOWN"
a={"prospective_checks":{"a":True,"b":False},"trigger_n":10,"baseline_n":100,"net_expected_after_hurdle":0.01}
b={"prospective_checks":{"a":True,"b":True},"trigger_n":1,"baseline_n":5,"net_expected_after_hurdle":-0.01}
assert m._score(b)>m._score(a)
assert m.execution_authority is False
print("[PASS] existing prospective edge status selector deterministic")
print("[EXECUTION_AUTHORITY] FALSE")
