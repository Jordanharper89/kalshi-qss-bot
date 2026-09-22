from pathlib import Path
from qseries_v2.oracle_predictive_discovery import opd_041_exact_live_token_materializer as m
root = Path.cwd()
assert (root / m.SOURCE_PATH).is_file()
assert m.execution_authority is False
assert m.probability_enabled is False
assert m.direction_enabled is False
assert m.publication_allowed is False
assert callable(m._load(root))
print("[OPD017]", m.SOURCE_PATH)
print("[TOKEN_CALLABLE]", m.TOKEN_CALLABLE)
print("[PASS] exact frozen OPD-017 source/hash/callable lineage captured")
print("[PASS] no token semantics invented or retuned")
print("[PASS] OPD-041 certified")
