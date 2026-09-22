from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
a={"asset":"BTC","observed_epoch":100.0}
rows=[(9,"source.crypto.hf.coinbase.historical_window","x",{"payload":{"observation_payload":{"product_id":"BTC-USD","window_seconds":5,"anchor_epoch":99,"return":.01}}}),(8,"source.crypto.condition.demo","crypto_condition_snapshot",{"raw_observation":{"payload":{"asset":"BTC","metric_name":"m","snapshot_at":98,"value":2,"direction":"up"}}}),(7,"source.crypto.learned_case.btc","crypto_verified_learned_case",{"raw_observation":{"payload":{"asset":"BTC","outcome_observed_at":97,"timing_certified":True,"condition_vector":["A"],"return_fraction":.02}}}),(6,"source.crypto.hf.coinbase.historical_window","x",{"payload":{"observation_payload":{"product_id":"BTC-USD","window_seconds":15,"anchor_epoch":101,"return":9}}})]
x=assemble(a,rows=rows)
assert x["coinbase_hf_state"]["5"]["state_epoch"]==99 and "15" not in x["coinbase_hf_state"]
assert x["crypto_condition_state"]["m"]["state_epoch"]==98 and x["learned_state"]["available_epoch"]==97
print("[PASS] OPD-062 strict as-of live world-state assembler certified")
