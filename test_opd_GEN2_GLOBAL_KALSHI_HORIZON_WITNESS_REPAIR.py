from qseries_v2.oracle_predictive_discovery.opd_051_exact_witnessed_future_path_outcome import materialize_from_path_and_witness
state={"state_id":"g2","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":300,"anchor_price":0.40}
path=[]
witness={"event_epoch":401.0,"sequence_number":999,"ticker":"KXOTHER","coverage_scope":"KALSHI_SOURCE_HIGHWATER"}
o=materialize_from_path_and_witness(state,path,witness)
assert o is not None
assert o["future_return"]==0.0
assert o["future_end_price"]==0.40
assert o["outcome_basis"]=="CARRY_FORWARD_NO_SAME_TICKER_EVENT_BEFORE_HORIZON"
assert o["coverage_witness_epoch"]==401.0
print("[PASS] global Kalshi highwater may witness horizon while same-ticker path remains isolated")
print("[PASS] sparse Gen2 300s state can resolve by carry-forward without fabricated ticker trade")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
