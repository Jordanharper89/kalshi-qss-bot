from qseries_v2.oracle_predictive_discovery.opd_048_exact_future_path_outcome_materializer import materialize_from_points
s={"state_id":"S","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":5,"anchor_price":.50}
pts=[{"ticker":"KXBTC","event_epoch":101.0,"price":.54,"sequence_number":1},{"ticker":"KXBTC","event_epoch":103.0,"price":.47,"sequence_number":2},{"ticker":"KXBTC","event_epoch":105.0,"price":.56,"sequence_number":3}]
x=materialize_from_points(s,pts);assert round(x["future_return"],8)==.06 and round(x["mfe"],8)==.06 and round(x["mae"],8)==-.03
assert x["resolution_epoch"]==105.0 and x["hit_plus_05"] and not x["hit_minus_05"]
assert materialize_from_points(s,pts[:-1]) is None
print("[5S_RETURN]",x["future_return"]);print("[MFE]",x["mfe"],"[MAE]",x["mae"]);print("[PASS] OPD-048 exact future path/outcome math certified; incomplete horizon abstains")
