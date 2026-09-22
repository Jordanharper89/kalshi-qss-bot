
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_021_holdout_feature_materialization_frozen_contract import build
s,p=build(Path.cwd());assert p.exists() and s["holdout_rows"]>0 and s["discovery_rows_read"]==0 and s["tokenization_contract"]=="EXACT_OPD017_FROZEN_RULES"
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[HOLDOUT_ROWS]",s["holdout_rows"]);print("[CRYPTO_ROWS]",s["crypto_rows"]);print("[CRYPTO_CORE_ROWS]",s["crypto_core_rows"]);print("[UNIQUE_TOKENS]",s["unique_tokens"]);print("[HORIZON_COUNTS]",s["horizon_counts"]);print("[PRIMITIVE_HASH]",s["primitive_hash"])
print("[PASS] untouched holdout contracts materialized with exact frozen OPD-017 token rules");print("[PASS] discovery rows not read");print("[PASS] OPD-021 holdout feature materialization certified")
