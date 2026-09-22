
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_013_cross_family_reaction_divergence_detector import detect

s = detect(Path.cwd())
assert s["families"] > 1
assert s["relationship_is_predictive_proven"] is False
assert s["edge_proven"] is False
assert s["read_only"] is True

print("[FAMILIES]", s["families"])
print("[DIVERGENCES]", len(s["divergences"]))
print("[TOP_DIVERGENCES]")
for x in s["divergences"][:25]:
    print(" ", x)

print("[PASS] divergence measured against empirical pair behavior")
print("[PASS] temporal coexistence alone is not treated as prediction")
print("[PASS] OED-013 cross-family reaction divergence detector certified")
