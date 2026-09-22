from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_012_live_event_normalization_and_intake import _read, normalize

def diagnose(root: Path, sample_limit: int = 100) -> dict:
    report_path = root / "OSI_011_LIVE_SOLANA_SOURCE_BOUNDARY.json"
    if not report_path.is_file():
        raise RuntimeError("Missing OSI-011 live source report")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    sources = []
    total_rows = 0
    normalized = 0
    failure_reasons = Counter()
    sample_shapes = []

    for src in report.get("live_sources", []):
        path = root / src["path"]
        rows = _read(path) if path.is_file() else []
        src_normalized = 0
        for row in rows[:sample_limit]:
            total_rows += 1
            if not isinstance(row, dict):
                failure_reasons["ROW_NOT_DICT"] += 1
                continue
            if len(sample_shapes) < 20:
                sample_shapes.append({
                    "source_path": src["path"],
                    "keys": sorted(row.keys()),
                    "sample": {k: row[k] for k in list(row.keys())[:20]},
                })
            event = normalize(row, src["path"])
            if event:
                normalized += 1
                src_normalized += 1
            else:
                has_asset = any(row.get(k) not in (None, "") for k in ("asset_key","mint","token_mint","address","pool_mint"))
                has_time = any(row.get(k) not in (None, "") for k in ("observed_at","timestamp","ts","created_at","block_time"))
                has_type = any(row.get(k) not in (None, "") for k in ("event_type","type","kind","event"))
                if not has_asset: failure_reasons["NO_RECOGNIZED_ASSET_FIELD"] += 1
                if not has_time: failure_reasons["NO_RECOGNIZED_TIME_FIELD"] += 1
                if not has_type: failure_reasons["NO_RECOGNIZED_EVENT_FIELD"] += 1
                if has_asset and has_time and has_type: failure_reasons["NORMALIZER_REJECTED_OTHER"] += 1
        sources.append({
            "path": src["path"],
            "rows_sampled": min(len(rows), sample_limit),
            "normalized_rows": src_normalized,
        })

    return {
        "revision": "OSI_022",
        "sources": sources,
        "rows_sampled_total": total_rows,
        "normalized_rows_total": normalized,
        "failure_reasons": dict(failure_reasons),
        "sample_shapes": sample_shapes,
        "execution_authority": False,
        "read_only": True,
    }

def write_report(root: Path) -> Path:
    data = diagnose(root)
    path = root / "OSI_022_LIVE_SOURCE_SHAPE_DIAGNOSTIC.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return path
