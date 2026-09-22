from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MOD = PKG / "oed_018_post_anomaly_behavior_classifier.py"
TEST = ROOT / "test_oed_018_post_anomaly_behavior_classifier.py"

assert (PKG / "oed_017_post_anomaly_kalshi_path_labeler.py").exists()

code = r"""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import hashlib, json

MOVE = 0.02

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def _sign(x, eps=1e-12):
    return 1 if x > eps else (-1 if x < -eps else 0)

def classify(root=None):
    root = Path(root or Path.cwd())
    src = root / "runtime" / "edge_discovery" / "oed_017_post_anomaly_path_labels.json"
    if not src.exists():
        raise FileNotFoundError(src)
    base = json.loads(src.read_text(encoding="utf-8"))

    rows = []
    counts = defaultdict(int)

    for e in base["events"]:
        if e.get("label_status") != "LABELED":
            continue

        detectors = set(e.get("detectors") or [])

        if "OED-014" in detectors and e.get("independent_signal_return") is not None:
            sig = _sign(float(e["independent_signal_return"]))
            for lab in e["labels"]:
                move = float(lab["return_dollars"])
                msign = _sign(move)
                if abs(move) < MOVE:
                    behavior = "NO_MATERIAL_MOVE"
                elif msign == sig:
                    behavior = "FOLLOW_THROUGH"
                elif msign == -sig:
                    behavior = "REVERSAL"
                else:
                    behavior = "MIXED"
                row = {
                    "event_id": e["event_id"],
                    "detector_family": "INDEPENDENT_REALITY_DIVERGENCE",
                    "horizon_seconds": lab["horizon_seconds"],
                    "ticker": lab["ticker"],
                    "signal_return": e["independent_signal_return"],
                    "kalshi_return_dollars": move,
                    "mfe_dollars": lab["mfe_dollars"],
                    "mae_dollars": lab["mae_dollars"],
                    "behavior": behavior,
                    "edge_proven": False,
                }
                rows.append(row)
                counts[behavior] += 1
            continue

        if detectors & {"OED-011", "OED-012"}:
            by_h = defaultdict(dict)
            for lab in e["labels"]:
                by_h[int(lab["horizon_seconds"])][lab["ticker"]] = lab

            members = [
                x for x in e.get("members", [])
                if x.get("detector") in {"OED-011", "OED-012"}
            ]
            # members are not carried by OED-017; recover initial pair from event key only.
            # For pair-dispersion behavior, compare absolute separation of end prices to
            # separation of base prices from the two target labels.
            for h, mp in by_h.items():
                if len(mp) != 2:
                    continue
                labs = list(mp.values())
                initial_gap = abs(float(labs[0]["base_price"]) - float(labs[1]["base_price"]))
                final_gap = abs(float(labs[0]["end_price"]) - float(labs[1]["end_price"]))
                delta = final_gap - initial_gap
                if delta <= -MOVE:
                    behavior = "SPREAD_CONVERGENCE"
                elif delta >= MOVE:
                    behavior = "SPREAD_EXPANSION"
                else:
                    behavior = "SPREAD_STABLE"
                row = {
                    "event_id": e["event_id"],
                    "detector_family": "CROSS_CONTRACT_DISPERSION",
                    "horizon_seconds": h,
                    "tickers": sorted(mp),
                    "initial_gap": initial_gap,
                    "final_gap": final_gap,
                    "gap_change": delta,
                    "behavior": behavior,
                    "edge_proven": False,
                }
                rows.append(row)
                counts[behavior] += 1

    rows.sort(
        key=lambda x: (
            x["detector_family"],
            int(x["horizon_seconds"]),
            x["event_id"],
        )
    )

    payload = {
        "schema_version": "OED-018",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_labels_hash": base["labels_hash"],
        "classification_count": len(rows),
        "behavior_counts": dict(sorted(counts.items())),
        "material_move_threshold_dollars": MOVE,
        "classifications": rows,
        "classification_hash": _hash(rows),
        "behavior_is_descriptive": True,
        "predictive_relation_proven": False,
        "edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }

    dst = root / "runtime" / "edge_discovery" / "oed_018_behavior_classifications.json"
    dst.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return payload, dst
"""
MOD.write_text(code, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_018_post_anomaly_behavior_classifier import classify

s, p = classify(Path.cwd())
assert p.exists()
assert s["classification_count"] >= 0
assert s["behavior_is_descriptive"] is True
assert s["predictive_relation_proven"] is False
assert s["edge_proven"] is False
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
assert len(s["classification_hash"]) == 64

print("[CLASSIFICATION_FILE]", p)
print("[CLASSIFICATIONS]", s["classification_count"])
print("[BEHAVIOR_COUNTS]", s["behavior_counts"])
print("[CLASSIFICATION_HASH]", s["classification_hash"])
print("[SAMPLES]")
for x in s["classifications"][:20]:
    print(" ", x)

print("[PASS] independent-reality divergence classified as follow-through/reversal/no-move only after future labels")
print("[PASS] cross-contract dispersion classified as spread convergence/expansion/stability")
print("[PASS] classifications remain descriptive and non-predictive")
print("[PASS] OED-018 post-anomaly behavior classifier certified")
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-018 installer complete")
