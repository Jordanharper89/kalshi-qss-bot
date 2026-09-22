from pathlib import Path
import json,math

PREDICTION_LEDGER_NAME="opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME_LEDGER_NAME="opd_full_evidence_live_outcome_ledger.jsonl"
SCOREBOARD_NAME="opd_full_evidence_live_profitability_scoreboard.json"
SCOREBOARD_REVISION="FULL_EVIDENCE_LIVE_PROFITABILITY_SCOREBOARD_V1"
ROUND_TRIP_HURDLE=0.02
execution_authority=False
publication_allowed=False

def _load(path):
    if not path.exists(): return []
    rows=[]
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try: rows.append(json.loads(line))
            except Exception: pass
    return rows

def _safe_mean(xs):
    return (sum(xs)/len(xs)) if xs else None

def _direction_hit(row):
    dr=float(row.get("directional_return") or 0.0)
    if dr>0: return 1.0
    if dr<0: return 0.0
    return 0.5

def _net_realized(row):
    return float(row.get("directional_return") or 0.0)-ROUND_TRIP_HURDLE

def _calibration_probability(row):
    p=float(row.get("predicted_probability") or 0.5)
    return max(0.0,min(1.0,p))

def build_scoreboard(root=None):
    root=Path(root or Path.cwd()).resolve()
    base=root/"runtime"/"predictive_data"
    preds=_load(base/PREDICTION_LEDGER_NAME)
    outs=_load(base/OUTCOME_LEDGER_NAME)
    resolved=[r for r in outs if r.get("resolution_status")=="RESOLVED_EXACT_FUTURE"]
    actionable=[r for r in resolved if bool(r.get("actionable_at_freeze"))]
    abstained=[r for r in resolved if not bool(r.get("actionable_at_freeze"))]

    def stats(rows):
        hits=[_direction_hit(r) for r in rows]
        dirrets=[float(r.get("directional_return") or 0.0) for r in rows]
        net=[_net_realized(r) for r in rows]
        probs=[_calibration_probability(r) for r in rows]
        brier=[(p-y)**2 for p,y in zip(probs,hits)]
        abs_cal=[abs(p-y) for p,y in zip(probs,hits)]
        positive=sum(1 for x in net if x>0)
        negative=sum(1 for x in net if x<0)
        flat=sum(1 for x in net if x==0)
        return {
          "n":len(rows),
          "hit_rate":_safe_mean(hits),
          "mean_directional_return":_safe_mean(dirrets),
          "mean_net_realized_after_2pct":_safe_mean(net),
          "cumulative_net_realized_after_2pct":sum(net) if net else 0.0,
          "positive_net_count":positive,
          "negative_net_count":negative,
          "flat_net_count":flat,
          "brier_score":_safe_mean(brier),
          "mean_absolute_calibration_error":_safe_mean(abs_cal),
          "mean_predicted_probability":_safe_mean(probs),
        }

    by_horizon={}
    for r in actionable:
        h=str(int(r.get("horizon_seconds") or 0))
        by_horizon.setdefault(h,[]).append(r)

    actionable_stats=stats(actionable)
    status="NO_RESOLVED_ACTIONABLE_PREDICTIONS"
    if actionable_stats["n"]>0:
        status="POSITIVE_NET_EXPECTANCY_OBSERVED" if actionable_stats["mean_net_realized_after_2pct"]>0 else "NONPOSITIVE_NET_EXPECTANCY_OBSERVED"

    board={
      "revision":SCOREBOARD_REVISION,
      "round_trip_hurdle":ROUND_TRIP_HURDLE,
      "prediction_rows":len(preds),
      "resolved_exact_future_rows":len(resolved),
      "actionable":actionable_stats,
      "abstained":stats(abstained),
      "actionable_by_horizon":{h:stats(rows) for h,rows in sorted(by_horizon.items(),key=lambda kv:int(kv[0]))},
      "profitability_status":status,
      "profitability_certified":False,
      "certification_note":"Observed prospective economics only; certification requires a sufficient untouched sample and separate acceptance rule.",
      "execution_authority":False,
      "publication_allowed":False,
    }
    path=base/SCOREBOARD_NAME
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(board,sort_keys=True,indent=2)+"\\n",encoding="utf-8")
    tmp.replace(path)
    board["scoreboard_path"]=str(path)
    return board

def run(root=None):
    b=build_scoreboard(root)
    a=b["actionable"]
    print("[LIVE PROFITABILITY SCOREBOARD] resolved_exact_future=",b["resolved_exact_future_rows"],
          "actionable_n=",a["n"],"status=",b["profitability_status"],flush=True)
    print("[ACTIONABLE] hit_rate=",a["hit_rate"],
          "mean_directional_return=",a["mean_directional_return"],
          "mean_net_after_2pct=",a["mean_net_realized_after_2pct"],
          "cumulative_net_after_2pct=",a["cumulative_net_realized_after_2pct"],flush=True)
    print("[CALIBRATION] brier=",a["brier_score"],
          "mean_abs_error=",a["mean_absolute_calibration_error"],
          "mean_predicted_probability=",a["mean_predicted_probability"],flush=True)
    print("[SCOREBOARD]",b["scoreboard_path"],flush=True)
    print("[PROFITABILITY_CERTIFIED] FALSE",flush=True)
    print("[EXECUTION/PUBLICATION] FALSE/FALSE",flush=True)
    return b

if __name__=="__main__":
    run()
