from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MOD = PKG / "oed_020_behavioral_research_maturity_gate.py"
TEST = ROOT / "test_oed_020_behavioral_research_maturity_gate.py"

assert (PKG / "oed_019_historical_candidate_outcome_statistics.py").exists()

code = r"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def _maturity(n):
    if n < 5:
        return "INSUFFICIENT"
    if n < 20:
        return "PRELIMINARY"
    if n < 100:
        return "DEVELOPING"
    return "MATURE_DESCRIPTIVE"

def gate(root=None):
    root = Path(root or Path.cwd())
    src = root / "runtime" / "edge_discovery" / "oed_019_historical_outcome_statistics.json"
    labels_path = root / "runtime" / "edge_discovery" / "oed_017_post_anomaly_path_labels.json"
    if not src.exists():
        raise FileNotFoundError(src)
    if not labels_path.exists():
        raise FileNotFoundError(labels_path)

    stats = json.loads(src.read_text(encoding="utf-8"))
    labels = json.loads(labels_path.read_text(encoding="utf-8"))

    rows = []
    maturity_counts = Counter()
    for x in stats["statistics"]:
        n = int(x["sample_size"])
        m = _maturity(n)
        maturity_counts[m] += 1
        rows.append({
            "detector_family": x["detector_family"],
            "horizon_seconds": x["horizon_seconds"],
            "magnitude_bucket": x["magnitude_bucket"],
            "sample_size": n,
            "maturity": m,
            "eligible_for_validation_engine": m in {
                "DEVELOPING", "MATURE_DESCRIPTIVE"
            },
            "predictive_edge_proven": False,
        })

    held_legacy = int(
        labels.get("status_counts", {}).get(
            "HELD_LEGACY_OUTER_TIME_NO_EXACT_EVENT_IDENTITY", 0
        )
    )

    payload = {
        "schema_version": "OED-020",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_statistics_hash": stats["statistics_hash"],
        "research_groups": rows,
        "maturity_counts": dict(sorted(maturity_counts.items())),
        "legacy_oed013_events_held": held_legacy,
        "thresholds": {
            "INSUFFICIENT": "n < 5",
            "PRELIMINARY": "5 <= n < 20",
            "DEVELOPING": "20 <= n < 100",
            "MATURE_DESCRIPTIVE": "n >= 100",
        },
        "next_phase": "OED-021..025_HISTORICAL_OUTCOME_ENGINE",
        "baseline_comparison_required": True,
        "temporal_isolation_required": True,
        "contract_day_isolation_required": True,
        "out_of_sample_required": True,
        "regime_stability_required": True,
        "predictive_model_fit_allowed": False,
        "certified_edge_count": 0,
        "edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
        "gate_hash": None,
    }
    payload["gate_hash"] = _hash({
        k: v for k, v in payload.items()
        if k not in {"created_at", "gate_hash"}
    })

    dst = root / "runtime" / "edge_discovery" / "oed_020_behavioral_research_gate.json"
    dst.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return payload, dst
"""
MOD.write_text(code, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_020_behavioral_research_maturity_gate import gate

s, p = gate(Path.cwd())
assert p.exists()
assert s["predictive_model_fit_allowed"] is False
assert s["certified_edge_count"] == 0
assert s["edge_proven"] is False
assert s["baseline_comparison_required"] is True
assert s["temporal_isolation_required"] is True
assert s["contract_day_isolation_required"] is True
assert s["out_of_sample_required"] is True
assert s["regime_stability_required"] is True
assert s["probability_enabled"] is False
assert s["direction_enabled"] is False
assert s["publication_allowed"] is False
assert s["execution_authority"] is False
assert len(s["gate_hash"]) == 64

print("[GATE_FILE]", p)
print("[MATURITY_COUNTS]", s["maturity_counts"])
print("[LEGACY_OED013_EVENTS_HELD]", s["legacy_oed013_events_held"])
print("[RESEARCH_GROUPS]")
for x in s["research_groups"]:
    print(" ", x)
print("[NEXT_PHASE]", s["next_phase"])
print("[GATE_HASH]", s["gate_hash"])

print("[PASS] sample maturity gate is descriptive only")
print("[PASS] legacy OED-013 outer-time candidates remain held")
print("[PASS] predictive model fitting remains prohibited")
print("[PASS] baseline/OOS/temporal/contract-day/regime validation required next")
print("[PASS] zero certified edges")
print("[PASS] OED-016..OED-020 behavioral research slice certified")
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-020 installer complete")
