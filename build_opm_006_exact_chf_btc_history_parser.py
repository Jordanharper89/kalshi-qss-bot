from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_pre_momentum"
PKG.mkdir(parents=True, exist_ok=True)
MODULE = PKG / "opm_006_exact_chf_btc_history_parser.py"
TEST = ROOT / "test_opm_006_exact_chf_btc_history_parser.py"

module = r"""
from pathlib import Path
import json
from datetime import datetime, timezone

REQUIRED = {
    "schema_version","product_id","anchor_epoch","anchor_time","window_seconds",
    "open_price","close_price","return","full_horizon_complete","past_only",
    "upstream_class","probability_enabled","direction_enabled",
    "publication_allowed","execution_authority"
}

def _parse_time(value):
    s = str(value).replace("Z","+00:00")
    d = datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def load_btc_history(root=None):
    root = Path(root or Path.cwd())
    path = root / "runtime" / "coinbase_hf" / "historical_condition_windows.jsonl"
    if not path.exists():
        raise FileNotFoundError(path)

    rows, rejected = [], []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            try:
                raw = json.loads(line)
            except Exception as exc:
                rejected.append((line_no, "INVALID_JSON", type(exc).__name__))
                continue
            missing = sorted(REQUIRED - set(raw))
            if missing:
                rejected.append((line_no, "MISSING_FIELDS", missing))
                continue
            if raw["product_id"] != "BTC-USD":
                continue
            if raw["schema_version"] != "CHF-016":
                rejected.append((line_no, "UNEXPECTED_SCHEMA", raw["schema_version"]))
                continue
            if raw["full_horizon_complete"] is not True or raw["past_only"] is not True:
                rejected.append((line_no, "NON_ADMISSIBLE_WINDOW", None))
                continue
            if raw["upstream_class"] != "RAW_EXTERNAL":
                rejected.append((line_no, "NOT_RAW_EXTERNAL", raw["upstream_class"]))
                continue
            if any(bool(raw[k]) for k in (
                "probability_enabled","direction_enabled",
                "publication_allowed","execution_authority"
            )):
                rejected.append((line_no, "SAFETY_FLAG_TRUE", None))
                continue

            rows.append({
                "anchor_epoch": int(raw["anchor_epoch"]),
                "anchor_time": _parse_time(raw["anchor_time"]),
                "window_seconds": int(raw["window_seconds"]),
                "open_price": float(raw["open_price"]),
                "close_price": float(raw["close_price"]),
                "return": float(raw["return"]),
                "event_count": int(raw.get("event_count", 0)),
                "max_event_gap_seconds": float(raw.get("max_event_gap_seconds", 0.0)),
                "boundary_age_seconds": float(raw.get("boundary_age_seconds", 0.0)),
                "source_line": line_no,
            })

    rows.sort(key=lambda r: (r["anchor_epoch"], r["window_seconds"]))
    return {"rows": rows, "rejected": rejected, "path": str(path)}

def group_by_anchor(rows):
    out = {}
    for row in rows:
        out.setdefault(row["anchor_epoch"], {})[row["window_seconds"]] = row
    return out
"""
MODULE.write_text(module, encoding="utf-8")

test = r"""
from pathlib import Path
from collections import Counter
from qseries_v2.oracle_pre_momentum.opm_006_exact_chf_btc_history_parser import load_btc_history, group_by_anchor

r = load_btc_history(Path.cwd())
rows = r["rows"]
assert rows, "no admissible BTC CHF history"
assert all(x["window_seconds"] in (5,15,30,60) for x in rows)
assert all(x["anchor_time"].tzinfo is not None for x in rows)
counts = Counter(x["window_seconds"] for x in rows)
anchors = group_by_anchor(rows)
complete = sum(all(w in v for w in (5,15,30,60)) for v in anchors.values())
print("[BTC_CHF_ROWS]", len(rows))
print("[WINDOW_COUNTS]", dict(sorted(counts.items())))
print("[ANCHORS]", len(anchors))
print("[COMPLETE_5_15_30_60_ANCHORS]", complete)
print("[REJECTED]", len(r["rejected"]))
print("[PASS] only CHF-016 RAW_EXTERNAL past-only complete BTC windows admitted")
print("[PASS] OPM-006 exact CHF BTC history parser certified")
"""
TEST.write_text(test, encoding="utf-8")
py_compile.compile(str(MODULE), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OPM-006 installer complete")
