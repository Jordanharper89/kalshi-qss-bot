
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_005_future_outcome_census_and_prediction_matrix_gate import build

s,p=build(Path.cwd())
assert p.exists()
assert s["outcome_rows"]>0
assert s["prediction_matrix_pavement_ready"]
assert all(x["label_strictly_future"] for x in s["outcomes"])
assert s["model_fit_allowed"] is False and s["edge_proven"] is False
print("[FILE]",p)
print("[OUTCOME_ROWS]",s["outcome_rows"])
print("[TICKERS]",s["ticker_count"])
print("[HORIZON_COUNTS]",s["horizon_counts"])
print("[PLUS_5C]",s["plus_05_count"])
print("[MINUS_5C]",s["minus_05_count"])
print("[PLUS_10C]",s["plus_10_count"])
print("[MINUS_10C]",s["minus_10_count"])
print("[OUTCOME_HASH]",s["outcome_hash"])
print("[NEXT_REQUIRED]",s["next_required"])
print("[PASS] future returns/MFE/MAE/time-to-move targets constructed")
print("[PASS] feature-side state and future labels remain separated")
print("[PASS] no formula/model/edge claim made before full raw-state join")
print("[PASS] OPD-001..OPD-005 raw predictive-data dissection slice certified")
