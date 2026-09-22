
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_005_edge_research_priority_surface import rank

s = rank(Path.cwd())
assert s["families_ranked"] > 0
assert s["ranking"]
assert s["edge_proven"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
scores = [x["research_priority_score"] for x in s["ranking"]]
assert scores == sorted(scores, reverse=True)
print("[FAMILIES_RANKED]", s["families_ranked"])
print("[TOP_RESEARCH_SURFACE]")
for i, row in enumerate(s["ranking"][:30], 1):
    print(f" {i:02d}.", row)
print("[PASS] physical Kalshi families ranked by depth/breadth/activity")
print("[PASS] source namespace matches are hints only, never evidence proof")
print("[PASS] no edge or probability was claimed")
print("[PASS] OED-001..OED-005 physical edge-surface inventory certified")
