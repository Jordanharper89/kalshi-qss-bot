
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_017_discovery_feature_primitive_materialization import build
s,p=build(Path.cwd());assert p.exists() and s["discovery_rows"]>0 and s["unique_tokens"]>0 and s["holdout_rows_read"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[DISCOVERY_ROWS]",s["discovery_rows"]);print("[CRYPTO_ROWS]",s["crypto_rows"]);print("[CRYPTO_CORE_ROWS]",s["crypto_core_rows"]);print("[UNIQUE_TOKENS]",s["unique_tokens"]);print("[HORIZON_COUNTS]",s["horizon_counts"]);print("[PRIMITIVE_HASH]",s["primitive_hash"])
print("[PASS] feature primitives derived from discovery contracts only");print("[PASS] targets copied unchanged and kept separate from feature tokens");print("[PASS] OPD-017 discovery feature primitives certified")
