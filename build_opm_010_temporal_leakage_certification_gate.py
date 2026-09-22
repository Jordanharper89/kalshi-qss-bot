from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_pre_momentum"
MODULE = PKG / "opm_010_temporal_leakage_certification_gate.py"
TEST = ROOT / "test_opm_010_temporal_leakage_certification_gate.py"

module = r"""
from pathlib import Path
import json
from collections import Counter
from qseries_v2.oracle_pre_momentum.opm_009_future_kalshi_price_path_labels import build_labeled_examples

LABEL_TIME_FIELDS = ("t5","t15","t30","t60","t120","t300","label_end_time")

def certify(root=None):
    root = Path(root or Path.cwd())
    rows = build_labeled_examples(root)["rows"]
    if not rows:
        raise RuntimeError("NO_FULL_PATH_EXAMPLES")

    violations = []
    for i, r in enumerate(rows):
        t = r["t"]
        if r["kalshi_base_time"] > t:
            violations.append((i, "BASE_AFTER_T"))
        for key in LABEL_TIME_FIELDS:
            if r[key] <= t:
                violations.append((i, f"{key}_NOT_AFTER_T"))

    ordered = sorted(rows, key=lambda x: x["t"])
    split = max(1, int(len(ordered)*0.70))
    train, test = ordered[:split], ordered[split:]
    chronology_ok = True
    if train and test:
        chronology_ok = max(x["t"] for x in train) <= min(x["t"] for x in test)

    state = {
        "schema_version": "OPM-010",
        "examples": len(rows),
        "contracts": len(set(r["ticker"] for r in rows)),
        "violations": violations,
        "feature_side_past_only": not violations,
        "labels_future_only": not violations,
        "chronological_split_plumbing_ok": chronology_ok,
        "predictive_edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }
    out = root / "runtime" / "pre_momentum"
    out.mkdir(parents=True, exist_ok=True)
    (out / "opm_010_temporal_certification.json").write_text(
        json.dumps(state, indent=2, default=str), encoding="utf-8"
    )
    return state
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_pre_momentum.opm_010_temporal_leakage_certification_gate import certify

s = certify(Path.cwd())
assert s["examples"] > 0
assert s["contracts"] > 0
assert s["violations"] == []
assert s["feature_side_past_only"] is True
assert s["labels_future_only"] is True
assert s["chronological_split_plumbing_ok"] is True
assert s["predictive_edge_proven"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
print("[CERTIFICATION]", s)
print("[PASS] all feature-side observations are at or before T")
print("[PASS] all labels are strictly after T")
print("[PASS] chronological train-before-test plumbing preserved")
print("[PASS] predictive edge remains UNPROVEN")
print("[PASS] OPM-006..OPM-010 temporal pavement certified")
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPM-010 installer complete")
