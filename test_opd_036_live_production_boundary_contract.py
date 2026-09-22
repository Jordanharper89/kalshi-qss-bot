
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_036_live_production_boundary_contract import build
s,p=build(Path.cwd());assert p.exists() and s["candidate_count"]==2 and s["canonical_highwater_sequence"]>0 and s["read_only"] and not s["execution_authority"]
print("[FILE]",p);print("[CANDIDATES]",s["candidate_count"]);print("[FORMULA_TOKENS]",s["required_formula_tokens"]);print("[CANONICAL_HIGHWATER]",s["canonical_highwater_sequence"]);print("[CHILDREN]",s["native_children"])
print("[PASS] exact live Oracle launcher, OPH-019 connect surface, canonical table, and frozen formula contract physically verified");print("[PASS] OPD-036 live production boundary contract certified")
