
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_007_temporal_family_coactivity_graph import build_graph
s=build_graph(Path.cwd())
assert s["minute_bins"]>0 and s["families"]>1 and s["edges"]
assert not s["causality_claimed"] and not s["edge_proven"] and s["read_only"]
print("[MINUTE_BINS]",s["minute_bins"]); print("[FAMILIES]",s["families"]); print("[EDGES]",len(s["edges"]))
print("[TOP_COACTIVITY]")
for x in s["edges"][:25]: print(" ",x)
print("[PASS] coactivity measured without causality claim")
print("[PASS] OED-007 temporal family coactivity graph certified")
