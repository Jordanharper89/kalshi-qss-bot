
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_016_contract_isolated_discovery_holdout_freeze import build
s,p=build(Path.cwd());assert p.exists() and s["discovery_ticker_count"]>0 and s["holdout_ticker_count"]>0
assert set(s["discovery_tickers"]).isdisjoint(s["holdout_tickers"]) and not s["holdout_visible_to_formula_discovery"]
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[TICKERS]",s["ticker_count"]);print("[DISCOVERY_TICKERS]",s["discovery_ticker_count"]);print("[HOLDOUT_TICKERS]",s["holdout_ticker_count"])
print("[ROW_COUNTS]",s["row_counts"]);print("[CRYPTO_ROWS]",s["crypto_row_counts"]);print("[CRYPTO_CORE_ROWS]",s["crypto_core_row_counts"]);print("[SPLIT_HASH]",s["split_hash"])
print("[PASS] whole tickers assigned to exactly one discovery/holdout partition");print("[PASS] holdout contracts remain invisible to formula discovery");print("[PASS] OPD-016 contract-isolated discovery/holdout freeze certified")
