from pathlib import Path
import json
import os

PREDICTION_LEDGER_NAME = "opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME_LEDGER_NAME = "opd_full_evidence_live_outcome_ledger.jsonl"
SCOREBOARD_NAME = "opd_full_evidence_live_profitability_scoreboard.json"
SCOREBOARD_REVISION = "FULL_EVIDENCE_LIVE_PROFITABILITY_SCOREBOARD_CLEAN_V1"
ROUND_TRIP_HURDLE = 0.02
EXECUTION_AUTHORITY = False
PUBLICATION_ALLOWED = False

def _read_jsonl(path):
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows

def _mean(values):
    return None if not values else sum(values) / len(values)

def _directional_hit(row):
    value = float(row.get("directional_return") or 0.0)
    if value > 0:
        return 1.0
    if value < 0:
        return 0.0
    return 0.5

def _stats(rows):
    hits = [_directional_hit(r) for r in rows]
    directional = [float(r.get("directional_return") or 0.0) for r in rows]
    net = [x - ROUND_TRIP_HURDLE for x in directional]
    probs = [max(0.0, min(1.0, float(r.get("predicted_probability") or 0.5))) for r in rows]
    brier = [(p - y) ** 2 for p, y in zip(probs, hits)]
    abs_cal = [abs(p - y) for p, y in zip(probs, hits)]
    return {
        "n": len(rows),
        "hit_rate": _mean(hits),
        "mean_directional_return": _mean(directional),
        "mean_net_realized_after_2pct": _mean(net),
        "cumulative_net_realized_after_2pct": sum(net) if net else 0.0,
        "positive_net_count": sum(1 for x in net if x > 0),
        "negative_net_count": sum(1 for x in net if x < 0),
        "flat_net_count": sum(1 for x in net if x == 0),
        "brier_score": _mean(brier),
        "mean_absolute_calibration_error": _mean(abs_cal),
        "mean_predicted_probability": _mean(probs),
    }

def build_scoreboard(root=None):
    root = Path(root or Path.cwd()).resolve()
    base = root / "runtime" / "predictive_data"
    predictions = _read_jsonl(base / PREDICTION_LEDGER_NAME)
    outcomes = _read_jsonl(base / OUTCOME_LEDGER_NAME)

    resolved = [r for r in outcomes if r.get("resolution_status") == "RESOLVED_EXACT_FUTURE"]
    actionable = [r for r in resolved if bool(r.get("actionable_at_freeze"))]
    abstained = [r for r in resolved if not bool(r.get("actionable_at_freeze"))]

    by_horizon = {}
    for row in actionable:
        h = str(int(row.get("horizon_seconds") or 0))
        by_horizon.setdefault(h, []).append(row)

    a = _stats(actionable)
    if a["n"] == 0:
        status = "NO_RESOLVED_ACTIONABLE_PREDICTIONS"
    elif a["mean_net_realized_after_2pct"] > 0:
        status = "POSITIVE_NET_EXPECTANCY_OBSERVED"
    else:
        status = "NONPOSITIVE_NET_EXPECTANCY_OBSERVED"

    by_generation_rows = {}
    for row in resolved:
        g = str(int(row.get("generation") or 2))
        by_generation_rows.setdefault(g, []).append(row)
    by_generation = {}
    for g, rows in sorted(by_generation_rows.items()):
        ga=[r for r in rows if bool(r.get("actionable_at_freeze"))]
        gs=_stats(ga)
        all_stats=_stats(rows)
        if gs["n"]==0:
            gst="NO_RESOLVED_ACTIONABLE_PREDICTIONS"
        elif gs["mean_net_realized_after_2pct"]>0:
            gst="POSITIVE_NET_EXPECTANCY_OBSERVED"
        else:
            gst="NONPOSITIVE_NET_EXPECTANCY_OBSERVED"
        by_generation[g]={
          "resolved_all":all_stats,
          "actionable":gs,
          "profitability_status":gst,
          "profitability_certified":False,
        }

    board = {
        "revision": SCOREBOARD_REVISION,
        "round_trip_hurdle": ROUND_TRIP_HURDLE,
        "prediction_rows": len(predictions),
        "resolved_exact_future_rows": len(resolved),
        "actionable": a,
        "by_generation": by_generation,
        "abstained": _stats(abstained),
        "actionable_by_horizon": {
            h: _stats(rows)
            for h, rows in sorted(by_horizon.items(), key=lambda item: int(item[0]))
        },
        "profitability_status": status,
        "profitability_certified": False,
        "certification_note": "Observed prospective economics only; certification requires a sufficient untouched live sample and separate acceptance rule.",
        "execution_authority": False,
        "publication_allowed": False,
    }

    path = base / SCOREBOARD_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(board, f, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)
    board["scoreboard_path"] = str(path)
    return board

def run(root=None):
    board = build_scoreboard(root)
    a = board["actionable"]
    print("[LIVE PROFITABILITY SCOREBOARD] resolved_exact_future=", board["resolved_exact_future_rows"],
          "actionable_n=", a["n"], "status=", board["profitability_status"], flush=True)
    print("[ACTIONABLE] hit_rate=", a["hit_rate"],
          "mean_directional_return=", a["mean_directional_return"],
          "mean_net_after_2pct=", a["mean_net_realized_after_2pct"],
          "cumulative_net_after_2pct=", a["cumulative_net_realized_after_2pct"], flush=True)
    print("[CALIBRATION] brier=", a["brier_score"],
          "mean_abs_error=", a["mean_absolute_calibration_error"],
          "mean_predicted_probability=", a["mean_predicted_probability"], flush=True)
    for g, block in sorted(board.get("by_generation", {}).items()):
        ga=block["actionable"]; gr=block["resolved_all"]
        print("[GENERATION]",g,
              "resolved_n=",gr["n"],
              "actionable_n=",ga["n"],
              "hit_rate=",ga["hit_rate"],
              "mean_net_after_2pct=",ga["mean_net_realized_after_2pct"],
              "cumulative_net_after_2pct=",ga["cumulative_net_realized_after_2pct"],
              "status=",block["profitability_status"], flush=True)
    print("[SCOREBOARD]", board["scoreboard_path"], flush=True)
    print("[PROFITABILITY_CERTIFIED] FALSE", flush=True)
    print("[EXECUTION/PUBLICATION] FALSE/FALSE", flush=True)
    return board

if __name__ == "__main__":
    run()
