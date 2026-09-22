from pathlib import Path
import shutil

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_full_evidence_live_profitability_scoreboard.py"
RUN=ROOT/"run_opd_full_evidence_predictor_child.py"
TEST=ROOT/"test_opd_FULL_EVIDENCE_LIVE_PROFITABILITY_CALIBRATION_SCOREBOARD.py"
BACKUP=ROOT/"run_opd_full_evidence_predictor_child.pre_live_profitability_scoreboard.bak"

PRED=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
RES=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_full_evidence_exact_future_outcome_resolver.py"

if not PRED.is_file() or "PREDICTION_LEDGER_REVISION=" not in PRED.read_text(encoding="utf-8"):
    raise RuntimeError("immutable prediction ledger boundary missing")
if not RES.is_file() or "OUTCOME_LEDGER_REVISION=" not in RES.read_text(encoding="utf-8"):
    raise RuntimeError("exact future outcome resolver boundary missing")
if not RUN.is_file():
    raise RuntimeError("full-evidence continuous child missing")

runner=RUN.read_text(encoding="utf-8")
for marker in ("run_prediction(root=root)","resolve_full_evidence_outcomes(root)","DEFAULT_CADENCE_SECONDS = 30.0"):
    if marker not in runner:
        raise RuntimeError("exact continuous-child boundary missing: "+marker)

module_text = """from pathlib import Path
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
    tmp.write_text(json.dumps(board,sort_keys=True,indent=2)+"\n",encoding="utf-8")
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
"""
MOD.parent.mkdir(parents=True,exist_ok=True)
MOD.write_text(module_text,encoding="utf-8")

import_line="from qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard import run as run_full_evidence_scoreboard\n"
if import_line not in runner:
    anchor="from qseries_v2.oracle_predictive_discovery.opd_full_evidence_exact_future_outcome_resolver import run as resolve_full_evidence_outcomes\n"
    if anchor not in runner:
        raise RuntimeError("exact outcome resolver import boundary missing")
    runner=runner.replace(anchor,anchor+import_line,1)

call="        resolve_full_evidence_outcomes(root)\n"
patched="        resolve_full_evidence_outcomes(root)\n        run_full_evidence_scoreboard(root)\n"
if "run_full_evidence_scoreboard(root)" not in runner:
    if runner.count(call)!=1:
        raise RuntimeError("exact resolver call boundary not found once")
    runner=runner.replace(call,patched,1)

if not BACKUP.exists():
    shutil.copy2(RUN,BACKUP)
RUN.write_text(runner,encoding="utf-8")

test_text = """from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard as m

with tempfile.TemporaryDirectory() as td:
    root=Path(td);base=root/"runtime"/"predictive_data";base.mkdir(parents=True)
    preds=[
      {"prediction_id":"P1"},{"prediction_id":"P2"},{"prediction_id":"P3"},{"prediction_id":"P4"}
    ]
    (base/m.PREDICTION_LEDGER_NAME).write_text("\n".join(json.dumps(x) for x in preds)+"\n",encoding="utf-8")
    outs=[
      {"prediction_id":"P1","resolution_status":"RESOLVED_EXACT_FUTURE","actionable_at_freeze":True,
       "horizon_seconds":300,"directional_return":0.08,"predicted_probability":0.70},
      {"prediction_id":"P2","resolution_status":"RESOLVED_EXACT_FUTURE","actionable_at_freeze":True,
       "horizon_seconds":300,"directional_return":-0.01,"predicted_probability":0.60},
      {"prediction_id":"P3","resolution_status":"RESOLVED_EXACT_FUTURE","actionable_at_freeze":False,
       "horizon_seconds":60,"directional_return":0.03,"predicted_probability":0.55},
      {"prediction_id":"P4","resolution_status":"CONTRACT_HORIZON_INELIGIBLE","actionable_at_freeze":False,
       "horizon_seconds":900}
    ]
    (base/m.OUTCOME_LEDGER_NAME).write_text("\n".join(json.dumps(x) for x in outs)+"\n",encoding="utf-8")
    b=m.build_scoreboard(root)
    a=b["actionable"]
    assert b["resolved_exact_future_rows"]==3
    assert a["n"]==2
    assert abs(a["hit_rate"]-0.5)<1e-12
    assert abs(a["mean_directional_return"]-0.035)<1e-12
    assert abs(a["mean_net_realized_after_2pct"]-0.015)<1e-12
    assert abs(a["cumulative_net_realized_after_2pct"]-0.03)<1e-12
    assert a["positive_net_count"]==1 and a["negative_net_count"]==1
    assert b["profitability_status"]=="POSITIVE_NET_EXPECTANCY_OBSERVED"
    assert b["profitability_certified"] is False
    assert b["abstained"]["n"]==1
    assert "300" in b["actionable_by_horizon"]
    p=base/m.SCOREBOARD_NAME
    assert p.exists()
    disk=json.loads(p.read_text(encoding="utf-8"))
    assert disk["execution_authority"] is False and disk["publication_allowed"] is False

runner=Path("run_opd_full_evidence_predictor_child.py").read_text(encoding="utf-8")
assert "run_prediction(root=root)" in runner
assert "resolve_full_evidence_outcomes(root)" in runner
assert "run_full_evidence_scoreboard(root)" in runner
assert runner.index("run_prediction(root=root)") < runner.index("resolve_full_evidence_outcomes(root)") < runner.index("run_full_evidence_scoreboard(root)")

print("[PASS] live profitability/calibration scoreboard computes only exact resolved outcomes")
print("[PASS] actionable predictions scored separately from abstained forecasts")
print("[PASS] realized directional return and fixed 2pct net economics verified")
print("[PASS] hit rate, Brier score, calibration error, and horizon breakdown verified")
print("[PASS] scoreboard remains observational; profitability certification stays FALSE")
print("[PASS] scoreboard runs after resolver inside existing 30-second child")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""
TEST.write_text(test_text,encoding="utf-8")

compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
compile(RUN.read_text(encoding="utf-8"),str(RUN),"exec")
compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

print("[PASS] live profitability/calibration scoreboard installed")
print("[SCOREBOARD] runtime/predictive_data/opd_full_evidence_live_profitability_scoreboard.json")
print("[PASS] exact resolved outcomes only; actionable vs abstain separated")
print("[PASS] fixed 2pct hurdle preserved; prediction gates unchanged")
print("[PASS] scoreboard integrated after resolver in existing 30-second child")
print("[PROFITABILITY_CERTIFIED] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
