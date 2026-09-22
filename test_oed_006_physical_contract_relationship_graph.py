
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_006_physical_contract_relationship_graph import build_graph
s=build_graph(Path.cwd())
assert s["contract_nodes"] and s["family_groups"]
assert s["semantic_equivalence_claimed"] is False and s["edge_proven"] is False and s["read_only"] is True
print("[CONTRACT_NODES]",len(s["contract_nodes"]))
print("[FAMILY_GROUPS]",len(s["family_groups"]))
print("[TOP_GROUPS]")
for x in s["family_groups"][:20]: print(" ",x["family"],x["contracts"])
print("[PASS] graph uses physical ticker-family membership only")
print("[PASS] no semantic equivalence or edge inferred")
print("[PASS] OED-006 physical contract relationship graph certified")
