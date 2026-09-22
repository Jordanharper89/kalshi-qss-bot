from __future__ import annotations
import hashlib
import json
from pathlib import Path

KEYWORDS = (
    "prediction", "fresh_candidates", "expired_skipped", "resolved_skipped",
    "source_prediction_count", "write", "persist", "json", "jsonl", "csv", "db",
    "BUY_PRESSURE", "created_at", "timestamp", "evaluated_at",
)

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _interesting_lines(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for number, line in enumerate(text.splitlines(), 1):
        lowered = line.lower()
        if any(k.lower() in lowered for k in KEYWORDS):
            out.append({"line": number, "text": line[:500]})
    return out[:300]

def _recent_candidate_files(root: Path) -> list[dict]:
    base = root / "runtime_state"
    if not base.exists():
        return []
    rows = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if not any(k in name for k in ("predict", "slop", "solana", "opportun", "thesis")):
            continue
        stat = path.stat()
        rows.append({
            "path": str(path.relative_to(root)),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        })
    rows.sort(key=lambda row: row["mtime_ns"], reverse=True)
    return rows[:200]

def audit(root: Path) -> dict:
    status_path = root / "runtime_state" / "oracle_opportunity_intelligence" / "registered_child_status.json"
    producer_path = root / "run_slop_buy_pressure_live.py"
    ooi_path = root / "qseries_v2" / "oracle_strategy_intelligence" / "oracle_opportunity_intelligence" / "ooi_026_registered_child_observation.py"

    if not status_path.is_file():
        raise RuntimeError(f"Missing live status: {status_path}")
    if not producer_path.is_file():
        raise RuntimeError(f"Missing registered producer: {producer_path}")
    if not ooi_path.is_file():
        raise RuntimeError(f"Missing registered OOI child module: {ooi_path}")

    status = json.loads(status_path.read_text(encoding="utf-8"))
    observation = status.get("observation") or {}
    total = int(observation.get("source_prediction_count") or 0)
    fresh = int(observation.get("fresh_candidates") or 0)
    expired = int(observation.get("expired_skipped") or 0)
    resolved = int(observation.get("resolved_skipped") or 0)
    future = int(observation.get("future_skipped") or 0)
    accounted = fresh + expired + resolved + future

    result = {
        "revision": "OOI_029",
        "purpose": "Trace why live BUY_PRESSURE source predictions are not replenishing fresh OOI candidates.",
        "execution_authority": False,
        "read_only": True,
        "registered_child_state": status.get("state"),
        "registered_child_round_count": status.get("round_count"),
        "source_prediction_count": total,
        "fresh_candidates": fresh,
        "expired_skipped": expired,
        "resolved_skipped": resolved,
        "future_skipped": future,
        "accounted_predictions": accounted,
        "prediction_accounting_exact": accounted == total,
        "supply_state": "FRESH_SUPPLY_PRESENT" if fresh else "NO_FRESH_SUPPLY",
        "producer": {
            "path": str(producer_path.relative_to(root)),
            "sha256_raw_windows_bytes": _sha256(producer_path),
            "interesting_lines": _interesting_lines(producer_path),
        },
        "ooi_reader": {
            "path": str(ooi_path.relative_to(root)),
            "sha256_raw_windows_bytes": _sha256(ooi_path),
            "interesting_lines": _interesting_lines(ooi_path),
        },
        "recent_candidate_files": _recent_candidate_files(root),
        "profitability_meaning": (
            "No fresh candidate means Oracle cannot freeze a new prospective thesis, "
            "paper-measure its 60-second path, or add a new clean outcome to learning."
        ),
        "certification": "LINEAGE_AUDIT_ONLY",
    }
    return result

def write_report(root: Path) -> Path:
    report = audit(root)
    path = root / "OOI_029_FRESH_CANDIDATE_SUPPLY_LINEAGE_AUDIT.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path
