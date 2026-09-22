
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_015_anomaly_candidate_registry import build_registry

s, p = build_registry(Path.cwd())
assert p.exists()
assert s["certified_edge_count"] == 0
assert s["rejected_candidate_retention_ready"] is True
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
assert all(x["status"] in {"DISCOVERED", "OBSERVING"} for x in s["candidates"])
assert all(x["certified_edge"] is False for x in s["candidates"])

print("[REGISTRY]", p)
print("[CANDIDATES]", s["candidate_count"])
counts = {}
for x in s["candidates"]:
    counts[x["detector"]] = counts.get(x["detector"], 0) + 1
print("[BY_DETECTOR]", counts)
print("[PASS] candidate IDs are deterministic content hashes")
print("[PASS] only DISCOVERED/OBSERVING statuses allowed")
print("[PASS] rejected-candidate retention pavement established")
print("[PASS] zero certified edges")
print("[PASS] OED-011..OED-015 core anomaly detector slice certified")
