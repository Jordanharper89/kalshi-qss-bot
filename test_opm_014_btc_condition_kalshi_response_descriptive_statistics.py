
from pathlib import Path
from pprint import pprint
from qseries_v2.oracle_pre_momentum.opm_014_btc_condition_kalshi_response_descriptive_statistics import describe

s = describe(Path.cwd())
assert s["rows"] > 0
assert s["contracts"] > 0
assert s["predictive_edge_proven"] is False
assert set(s["features"]) == {"btc_return_5s","btc_return_15s","btc_return_30s","btc_return_60s"}
assert set(s["responses"]) == {"d5","d15","d30","d60","d120","d300"}
print("[DESCRIPTIVE_STATISTICS]")
pprint(s)
print("[PASS] BTC condition distributions measured")
print("[PASS] Kalshi future response distributions measured")
print("[PASS] statistics remain descriptive only; no edge claim permitted")
print("[PASS] OPM-014 BTC condition x Kalshi response descriptive statistics certified")
