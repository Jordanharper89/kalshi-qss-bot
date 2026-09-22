
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_010_relationship_surface_snapshot_freeze import freeze
s,p=freeze(Path.cwd())
assert p.exists() and len(s["content_sha256"])==64
assert s["contract_graph"]["contract_nodes"]
assert s["coactivity_graph"]["edges"]
assert s["source_market_overlap_graph"]["edges"]
assert s["trade_surface"]["families"]
assert not s["edge_proven"] and not s["probability_enabled"] and not s["publication_allowed"] and not s["execution_authority"]
print("[SNAPSHOT]",p)
print("[SHA256]",s["content_sha256"])
print("[CONTRACT_NODES]",len(s["contract_graph"]["contract_nodes"]))
print("[COACTIVITY_EDGES]",len(s["coactivity_graph"]["edges"]))
print("[SOURCE_MARKET_EDGES]",len(s["source_market_overlap_graph"]["edges"]))
print("[TRADE_ACTIVE_FAMILIES]",len(s["trade_surface"]["families"]))
print("[PASS] relationship discovery inputs frozen into one reproducible snapshot")
print("[PASS] snapshot is research pavement, not edge certification")
print("[PASS] OED-006..OED-010 relationship and contract graph slice certified")
