
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_011_cross_contract_inconsistency_detector import detect

s = detect(Path.cwd())
assert s["families_scanned"] > 0
assert s["semantic_inconsistency_proven"] is False
assert s["edge_proven"] is False
assert s["read_only"] is True

print("[FAMILIES_SCANNED]", s["families_scanned"])
print("[ANOMALIES]", len(s["anomalies"]))
print("[TOP_ANOMALIES]")
for x in s["anomalies"][:25]:
    print(" ", x)

print("[PASS] detector is descriptive only")
print("[PASS] no semantic ordering was guessed")
print("[PASS] no edge was certified")
print("[PASS] OED-011 cross-contract inconsistency detector certified")
