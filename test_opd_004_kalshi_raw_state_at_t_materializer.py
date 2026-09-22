
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_004_kalshi_raw_state_at_t_materializer import materialize

s,p=materialize(Path.cwd())
assert p.exists() and s["row_count"]>0 and s["ticker_count"]>0
assert all(x["feature_side_only"] for x in s["rows"])
assert not s["derived_prediction_features_created"]
print("[FILE]",p)
print("[ROWS]",s["row_count"])
print("[TICKERS]",s["ticker_count"])
print("[OBSERVATION_TYPES]",s["observation_types"])
print("[EVENT_TIME_PATHS]",s["event_time_paths"])
print("[STATE_HASH]",s["state_hash"])
print("[SAMPLES]")
for x in s["rows"][-10:]: print(" ",x)
print("[PASS] physical Kalshi state-at-T materialized without model assumptions")
print("[PASS] raw market/microstructure fields preserved before derivation")
print("[PASS] OPD-004 Kalshi raw state-at-T materializer certified")
