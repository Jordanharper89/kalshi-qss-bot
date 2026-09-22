from qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome import materialize_from_path_and_witness
s={"state_id":"S051","ticker":"KXTEST","observed_epoch":100.0,"horizon_seconds":5,"anchor_price":.50}
p=[{"ticker":"KXTEST","event_epoch":101.0,"price":.52,"sequence_number":1},{"ticker":"KXTEST","event_epoch":104.0,"price":.57,"sequence_number":2}]
w={"ticker":"KXTEST","event_epoch":106.0,"price":.56,"sequence_number":3}
x=materialize_from_path_and_witness(s,p,w)
assert round(x["future_return"],8)==.07 and round(x["mfe"],8)==.07
assert x["resolution_epoch"]==105.0 and x["coverage_witness_epoch"]==106.0 and x["hit_plus_05"] is True
assert materialize_from_path_and_witness(s,p,None) is None
print("[ENDPOINT]",x["future_end_price"],"[WITNESS]",x["coverage_witness_epoch"])
print("[PASS] OPD-051 OPD-005-compatible witnessed future path semantics certified")
