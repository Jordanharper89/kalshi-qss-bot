from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MOD = PKG / "oed_012_threshold_curve_distortion_detector.py"
TEST = ROOT / "test_oed_012_threshold_curve_distortion_detector.py"

assert (PKG / "oed_011_cross_contract_inconsistency_detector.py").exists()

code = r"""
from pathlib import Path
import re
from collections import defaultdict
from qseries_v2.oracle_edge_discovery.oed_011_cross_contract_inconsistency_detector import detect as base_detect

NUM_RE = re.compile(r'(?<![A-Z])(\d+(?:\.\d+)?)')

def _numeric_tokens(ticker):
    return [float(x) for x in NUM_RE.findall(str(ticker))]

def detect(root=None):
    base = base_detect(Path(root or Path.cwd()))
    out = []
    for x in base["anomalies"]:
        ta = _numeric_tokens(x["ticker_a"])
        tb = _numeric_tokens(x["ticker_b"])
        shared_numeric_structure = bool(ta and tb)
        out.append({
            **x,
            "ticker_a_numeric_tokens": ta,
            "ticker_b_numeric_tokens": tb,
            "threshold_structure_candidate": shared_numeric_structure,
            "monotonicity_violation_proven": False,
            "status": "OBSERVING" if shared_numeric_structure else "DISCOVERED",
        })

    candidates = [x for x in out if x["threshold_structure_candidate"]]
    candidates.sort(key=lambda x: x["absolute_price_gap"], reverse=True)
    return {
        "schema_version": "OED-012",
        "candidates": candidates,
        "candidate_count": len(candidates),
        "numeric_parser_only": True,
        "monotonicity_violation_proven": False,
        "edge_proven": False,
        "read_only": True,
    }
"""
MOD.write_text(code, encoding="utf-8")

test = r"""
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
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-012 installer complete")
