
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_012_threshold_curve_distortion_detector import detect

s = detect(Path.cwd())
assert s["numeric_parser_only"] is True
assert s["monotonicity_violation_proven"] is False
assert s["edge_proven"] is False
assert s["read_only"] is True

print("[THRESHOLD_STRUCTURE_CANDIDATES]", s["candidate_count"])
print("[TOP_CANDIDATES]")
for x in s["candidates"][:25]:
    print(" ", x)

print("[PASS] ticker numeric structure measured without proposition guessing")
print("[PASS] monotonicity violation not declared without exact threshold semantics")
print("[PASS] OED-012 threshold-curve distortion detector certified")
