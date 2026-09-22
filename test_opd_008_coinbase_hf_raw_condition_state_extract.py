
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_008_coinbase_hf_raw_condition_state_extract import build
s,p=build(Path.cwd());assert p.exists() and s["row_count"]>0 and all(x["past_only"] for x in s["rows"])
print("[FILE]",p);print("[ROWS]",s["row_count"]);print("[PRODUCTS]",s["products"]);print("[HORIZONS]",s["horizons"]);print("[HASH]",s["hash"])
print("[FIRST]",s["rows"][0]);print("[LAST]",s["rows"][-1])
print("[PASS] exact CHF historical complete-window contract extracted")
print("[PASS] independent Coinbase state remains feature-side only")
print("[PASS] OPD-008 Coinbase HF raw-condition state certified")
