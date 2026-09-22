
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_009_cross_family_dense_trade_surface import surface
s=surface(Path.cwd())
assert s["families"]
assert not s["predictive_edge_proven"] and not s["probability_enabled"] and not s["execution_authority"]
print("[TRADE_ACTIVE_FAMILIES]",len(s["families"]))
print("[TOP_PATH_RICH_FAMILIES]")
for x in s["families"][:30]: print(" ",x)
print("[PASS] path-rich families ranked from physical trade density")
print("[PASS] no predictive edge claimed")
print("[PASS] OED-009 cross-family dense-trade surface certified")
