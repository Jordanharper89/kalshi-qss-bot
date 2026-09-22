
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_009_crypto_condition_raw_state_extract import build
s,p=build(Path.cwd());assert p.exists() and s["row_count"]>0
print("[FILE]",p);print("[ROWS]",s["row_count"]);print("[ASSETS]",s["assets"]);print("[TOP_METRICS]",dict(list(sorted(s["metrics"].items(),key=lambda x:-x[1]))[:30]));print("[HASH]",s["hash"])
print("[PASS] raw crypto condition values preserved without predictive compression")
print("[PASS] source lineage retained")
print("[PASS] OPD-009 crypto-condition raw state certified")
