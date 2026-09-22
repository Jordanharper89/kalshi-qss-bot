from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MOD = PKG / "oed_019_historical_candidate_outcome_statistics.py"
TEST = ROOT / "test_oed_019_historical_candidate_outcome_statistics.py"

assert (PKG / "oed_018_post_anomaly_behavior_classifier.py").exists()

code = r"""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter
from statistics import mean, median
import hashlib, json

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def _magnitude_bucket(row):
    if row["detector_family"] == "INDEPENDENT_REALITY_DIVERGENCE":
        x = abs(float(row.get("signal_return", 0.0)))
        if x < 0.0005:
            return "LT_5BP"
        if x < 0.0010:
            return "5_TO_10BP"
        return "GE_10BP"

    x = abs(float(row.get("initial_gap", 0.0)))
    if x < 0.20:
        return "LT_20C"
    if x < 0.40:
        return "20_TO_40C"
    return "GE_40C"

def aggregate(root=None):
    root = Path(root or Path.cwd())
    src = root / "runtime" / "edge_discovery" / "oed_018_behavior_classifications.json"
    if not src.exists():
        raise FileNotFoundError(src)
    base = json.loads(src.read_text(encoding="utf-8"))

    groups = defaultdict(list)
    for x in base["classifications"]:
        key = (
            x["detector_family"],
            int(x["horizon_seconds"]),
            _magnitude_bucket(x),
        )
        groups[key].append(x)

    stats = []
    for (family, horizon, bucket), rows in sorted(groups.items()):
        behaviors = Counter(x["behavior"] for x in rows)
        item = {
            "detector_family": family,
            "horizon_seconds": horizon,
            "magnitude_bucket": bucket,
            "sample_size": len(rows),
            "behavior_counts": dict(sorted(behaviors.items())),
            "behavior_frequencies": {
                k: v / len(rows) for k, v in sorted(behaviors.items())
            },
            "predictive_probability_enabled": False,
            "edge_proven": False,
        }

        if family == "INDEPENDENT_REALITY_DIVERGENCE":
            vals = [float(x["kalshi_return_dollars"]) for x in rows]
            item["mean_kalshi_return_dollars"] = mean(vals)
            item["median_kalshi_return_dollars"] = median(vals)
            item["mean_mfe_dollars"] = mean(float(x["mfe_dollars"]) for x in rows)
            item["mean_mae_dollars"] = mean(float(x["mae_dollars"]) for x in rows)
        else:
            vals = [float(x["gap_change"]) for x in rows]
            item["mean_gap_change_dollars"] = mean(vals)
            item["median_gap_change_dollars"] = median(vals)

        stats.append(item)

    payload = {
        "schema_version": "OED-019",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_classification_hash": base["classification_hash"],
        "group_count": len(stats),
        "statistics": stats,
        "statistics_hash": _hash(stats),
        "raw_frequency_only": True,
        "baseline_comparison_complete": False,
        "out_of_sample_validation_complete": False,
        "edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
    }

    dst = root / "runtime" / "edge_discovery" / "oed_019_historical_outcome_statistics.json"
    dst.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return payload, dst
"""
MOD.write_text(code, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_019_historical_candidate_outcome_statistics import aggregate

s, p = aggregate(Path.cwd())
assert p.exists()
assert s["group_count"] >= 0
assert s["raw_frequency_only"] is True
assert s["baseline_comparison_complete"] is False
assert s["out_of_sample_validation_complete"] is False
assert s["edge_proven"] is False
assert s["probability_enabled"] is False
assert s["execution_authority"] is False
assert len(s["statistics_hash"]) == 64

print("[STATISTICS_FILE]", p)
print("[GROUPS]", s["group_count"])
print("[STATISTICS_HASH]", s["statistics_hash"])
print("[GROUP_STATS]")
for x in s["statistics"]:
    print(" ", x)

print("[PASS] outcomes aggregated by detector family, horizon, and magnitude bucket")
print("[PASS] sample size and raw behavior frequencies preserved")
print("[PASS] no raw frequency promoted to predictive probability")
print("[PASS] baseline and out-of-sample validation remain incomplete")
print("[PASS] OED-019 historical candidate outcome statistics certified")
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-019 installer complete")
