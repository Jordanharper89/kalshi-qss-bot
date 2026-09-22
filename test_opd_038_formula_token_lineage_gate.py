
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_038_formula_token_lineage_gate import build
s,p=build(Path.cwd());assert p.exists() and s["all_tokens_physically_observed"] and s["exact_opd017_rules_required"]
print("[FILE]",p);print("[REQUIRED_TOKENS]",s["required_tokens"]);print("[TOKEN_LINEAGES]",s["token_lineages"]);print("[PASS] every frozen formula token traced to physical OPD-017/021 observations");print("[PASS] OPD-038 formula-token lineage gate certified")
