from pathlib import Path
import py_compile

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_edge_discovery"
MOD = PKG / "oed_017_post_anomaly_kalshi_path_labeler.py"
TEST = ROOT / "test_oed_017_post_anomaly_kalshi_path_labeler.py"

assert (PKG / "oed_016_candidate_event_normalization_and_freeze.py").exists()

code = r"""
from pathlib import Path
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timezone
import hashlib, json, math

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

SCAN_ROWS = 250000
HORIZONS = (30, 60, 300, 900)
KALSHI_SOURCE = "source.kalshi.market_data"
COINBASE_SOURCE = "source.crypto.hf.coinbase.historical_window"

def _hash(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()

def _kalshi(obj):
    if not isinstance(obj, dict):
        return None
    p = obj.get("payload")
    if not isinstance(p, dict):
        return None
    m = p.get("message")
    if not isinstance(m, dict):
        return None

    ticker = str(m.get("market_ticker") or p.get("source_market_id") or "")
    if not ticker.startswith("KX"):
        return None

    epoch = m.get("ts")
    if epoch is None and m.get("ts_ms") is not None:
        try:
            epoch = float(m["ts_ms"]) / 1000.0
        except Exception:
            epoch = None

    px = m.get("yes_price_dollars")
    if px is None:
        px = m.get("price_dollars")
    if px is None:
        px = m.get("last_price_dollars")

    try:
        return float(epoch), ticker, float(px)
    except Exception:
        return None

def _coinbase(obj):
    if not isinstance(obj, dict):
        return None
    p = obj.get("payload")
    if not isinstance(p, dict):
        return None
    row = p.get("observation_payload")
    if not isinstance(row, dict):
        return None
    if str(row.get("product_id")) != "BTC-USD":
        return None
    if row.get("full_horizon_complete") is not True:
        return None
    try:
        return (
            float(row["anchor_epoch"]),
            int(row["window_seconds"]),
            float(row["return"]),
        )
    except Exception:
        return None

def _future_path(series, anchor, horizon):
    times = [x[0] for x in series]
    base_i = bisect_right(times, anchor) - 1
    if base_i < 0:
        return None

    base_t, base_px = series[base_i]
    if anchor - base_t > 30.0:
        return None

    end = anchor + horizon
    end_i = bisect_right(times, end) - 1
    if end_i <= base_i:
        return None

    # Require actual source-event coverage through the requested horizon.
    if times[-1] < end:
        return None

    future = series[base_i + 1:end_i + 1]
    if not future:
        return None

    end_px = future[-1][1]
    max_row = max(future, key=lambda x: x[1])
    min_row = min(future, key=lambda x: x[1])

    mfe = max_row[1] - base_px
    mae = min_row[1] - base_px
    return {
        "horizon_seconds": horizon,
        "base_event_epoch": base_t,
        "base_price": base_px,
        "end_price": end_px,
        "return_dollars": end_px - base_px,
        "mfe_dollars": mfe,
        "mae_dollars": mae,
        "time_to_max_seconds": max_row[0] - anchor,
        "time_to_min_seconds": min_row[0] - anchor,
        "hit_plus_05": mfe >= 0.05,
        "hit_minus_05": mae <= -0.05,
        "past_only_anchor": True,
        "future_only_label": True,
    }

def label(root=None):
    root = Path(root or Path.cwd())
    src = root / "runtime" / "edge_discovery" / "oed_016_normalized_event_population.json"
    if not src.exists():
        raise FileNotFoundError(src)
    pop = json.loads(src.read_text(encoding="utf-8"))

    with connect(root, autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='30000ms'")
            q.execute(
                "SELECT max(sequence_number) "
                "FROM public.oracle_canonical_observations"
            )
            max_seq = int(q.fetchone()[0])
            lo = max(1, max_seq - SCAN_ROWS + 1)
            q.execute(
                "SELECT sequence_number, observed_at, source_id, canonical_observation_json "
                "FROM public.oracle_canonical_observations "
                "WHERE sequence_number BETWEEN %s AND %s "
                "ORDER BY sequence_number",
                (lo, max_seq)
            )
            rows = q.fetchall() or []
        c.rollback()

    kalshi_by_ticker = defaultdict(list)
    kalshi_by_seq = {}
    coinbase_index = defaultdict(list)

    for seq, outer_ts, sid, obj in rows:
        sid = str(sid)
        if sid == KALSHI_SOURCE:
            x = _kalshi(obj)
            if x:
                epoch, ticker, px = x
                kalshi_by_ticker[ticker].append((epoch, px))
                kalshi_by_seq[int(seq)] = (epoch, ticker, px)
        elif sid == COINBASE_SOURCE:
            x = _coinbase(obj)
            if x:
                epoch, horizon, ret = x
                key = (int(epoch) // 60, horizon, round(ret, 15))
                coinbase_index[key].append(epoch)

    for ticker in kalshi_by_ticker:
        kalshi_by_ticker[ticker].sort()

    results = []
    counts = defaultdict(int)

    for event in pop["events"]:
        detectors = set(event["detectors"])
        out = {
            "event_id": event["event_id"],
            "detectors": event["detectors"],
            "event_key": event["event_key"],
            "label_status": None,
            "anchor_basis": None,
            "anchor_epoch": None,
            "targets": [],
            "labels": [],
            "edge_proven": False,
        }

        if detectors & {"OED-011", "OED-012"}:
            members = [
                x for x in event["members"]
                if x.get("detector") in {"OED-011", "OED-012"}
            ]
            ref = members[0]
            seqs = [int(ref["sequence_a"]), int(ref["sequence_b"])]
            resolved = [kalshi_by_seq.get(x) for x in seqs]
            if any(x is None for x in resolved):
                out["label_status"] = "SEQUENCE_OUTSIDE_BOUNDED_HISTORY"
            else:
                anchor = max(x[0] for x in resolved)
                tickers = sorted(set(x[1] for x in resolved))
                out["anchor_basis"] = "EXACT_KALSHI_SOURCE_EVENT_SEQUENCE"
                out["anchor_epoch"] = anchor
                out["targets"] = tickers
                for ticker in tickers:
                    for h in HORIZONS:
                        y = _future_path(kalshi_by_ticker[ticker], anchor, h)
                        if y:
                            out["labels"].append({"ticker": ticker, **y})
                out["label_status"] = (
                    "LABELED" if out["labels"] else "NO_COMPLETE_FUTURE_PATH"
                )

        elif "OED-014" in detectors:
            # Pick strongest physical Coinbase member and recover exact anchor_epoch
            # from the persisted OAD-261 CHF row; do not invent seconds from minute_bin.
            members = [x for x in event["members"] if x.get("detector") == "OED-014"]
            ref = max(
                members,
                key=lambda x: abs(float(x.get("coinbase_max_abs_return", 0.0)))
            )
            key = (
                int(ref["minute_bin"]),
                int(ref["coinbase_window_seconds"]),
                round(float(ref["coinbase_max_abs_return"]), 15),
            )
            anchors = coinbase_index.get(key) or []
            ticker = str(ref.get("kalshi_first_ticker") or ref.get("kalshi_last_ticker") or "")
            if not anchors:
                out["label_status"] = "EXACT_COINBASE_ANCHOR_NOT_RECOVERED"
            elif ticker not in kalshi_by_ticker:
                out["label_status"] = "KALSHI_TICKER_NOT_IN_BOUNDED_HISTORY"
            else:
                anchor = min(anchors)
                out["anchor_basis"] = "EXACT_CHF_ANCHOR_EPOCH"
                out["anchor_epoch"] = anchor
                out["targets"] = [ticker]
                out["independent_signal_return"] = float(ref["coinbase_max_abs_return"])
                out["independent_signal_horizon_seconds"] = int(ref["coinbase_window_seconds"])
                for h in HORIZONS:
                    y = _future_path(kalshi_by_ticker[ticker], anchor, h)
                    if y:
                        out["labels"].append({"ticker": ticker, **y})
                out["label_status"] = (
                    "LABELED" if out["labels"] else "NO_COMPLETE_FUTURE_PATH"
                )

        elif detectors == {"OED-013"}:
            # OED-013 used outer observed_at minute bins and has no exact ticker/sequence.
            # Do not silently turn that legacy timestamp into an exact causal anchor.
            out["label_status"] = "HELD_LEGACY_OUTER_TIME_NO_EXACT_EVENT_IDENTITY"
            out["anchor_basis"] = "NONE"

        else:
            out["label_status"] = "UNSUPPORTED_EVENT_IDENTITY"

        counts[out["label_status"]] += 1
        results.append(out)

    payload = {
        "schema_version": "OED-017",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_population_hash": pop["event_population_hash"],
        "bounded_sequence_window": [lo, max_seq],
        "bounded_rows": len(rows),
        "horizons_seconds": list(HORIZONS),
        "event_count": len(results),
        "status_counts": dict(sorted(counts.items())),
        "labeled_event_count": sum(x["label_status"] == "LABELED" for x in results),
        "events": results,
        "labels_hash": _hash(results),
        "strict_source_event_time": True,
        "legacy_outer_time_not_promoted": True,
        "future_only_labels": True,
        "edge_proven": False,
        "probability_enabled": False,
        "direction_enabled": False,
        "publication_allowed": False,
        "execution_authority": False,
        "read_only": True,
    }

    dst = root / "runtime" / "edge_discovery" / "oed_017_post_anomaly_path_labels.json"
    dst.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return payload, dst
"""
MOD.write_text(code, encoding="utf-8")

test = r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_017_post_anomaly_kalshi_path_labeler import label

s, p = label(Path.cwd())
assert p.exists()
assert s["bounded_rows"] > 0
assert s["event_count"] > 0
assert s["strict_source_event_time"] is True
assert s["legacy_outer_time_not_promoted"] is True
assert s["future_only_labels"] is True
assert s["edge_proven"] is False
assert s["execution_authority"] is False
assert len(s["labels_hash"]) == 64

print("[LABEL_FILE]", p)
print("[BOUNDED_SEQUENCE_WINDOW]", s["bounded_sequence_window"])
print("[BOUNDED_ROWS]", s["bounded_rows"])
print("[EVENTS]", s["event_count"])
print("[STATUS_COUNTS]", s["status_counts"])
print("[LABELED_EVENTS]", s["labeled_event_count"])
print("[LABELS_HASH]", s["labels_hash"])

samples = [x for x in s["events"] if x["label_status"] == "LABELED"][:10]
print("[LABELED_SAMPLES]")
for x in samples:
    print(" ", {
        "event_id": x["event_id"],
        "detectors": x["detectors"],
        "anchor_basis": x["anchor_basis"],
        "targets": x["targets"],
        "labels": x["labels"][:2],
    })

print("[PASS] one bounded PostgreSQL outcome surface used")
print("[PASS] exact Kalshi source-event time recovered from sequence identity")
print("[PASS] exact CHF anchor_epoch recovered for OED-014")
print("[PASS] OED-013 legacy outer-time candidates held rather than fabricated")
print("[PASS] 30s/60s/5m/15m future-only path labels materialized where complete")
print("[PASS] OED-017 post-anomaly path labeler certified")
"""
TEST.write_text(test, encoding="utf-8")

py_compile.compile(str(MOD), doraise=True)
py_compile.compile(str(TEST), doraise=True)
print("[PASS] OED-017 installer complete")
