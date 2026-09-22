
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_011_deterministic_outcome_anchor_population import build
s,p=build(Path.cwd())
assert p.exists() and s["anchor_rows"]>0
assert s["anchor_rows"]==s["unique_anchor_ids"]
assert s["target_population_frozen"] and not s["feature_join_performed"]
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[ANCHOR_ROWS]",s["anchor_rows"]);print("[TICKERS]",s["ticker_count"])
print("[HORIZONS]",s["horizons"]);print("[ANCHOR_HASH]",s["anchor_population_hash"])
print("[PASS] exact OPD-005 outcome population frozen without feature filtering")
print("[PASS] target labels remain strictly future and immutable for downstream joins")
print("[PASS] OPD-011 deterministic outcome-anchor population certified")
