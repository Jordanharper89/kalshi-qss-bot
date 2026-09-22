
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_008_source_market_temporal_overlap_graph import build_graph
s=build_graph(Path.cwd())
assert s["market_bins"]>0 and s["source_bins"]>0 and s["edges"]
assert not s["source_is_independent_evidence_proven"] and not s["causality_claimed"] and not s["edge_proven"]
print("[MARKET_BINS]",s["market_bins"]); print("[SOURCE_BINS]",s["source_bins"]); print("[EDGES]",len(s["edges"]))
print("[TOP_OVERLAPS]")
for x in s["edges"][:30]: print(" ",x)
print("[PASS] source-market temporal overlap measured")
print("[PASS] overlap does not declare evidence independence or causality")
print("[PASS] OED-008 source-market temporal overlap graph certified")
