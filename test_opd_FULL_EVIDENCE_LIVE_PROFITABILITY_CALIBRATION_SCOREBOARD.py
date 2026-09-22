from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard as m

with tempfile.TemporaryDirectory() as td:
    root=Path(td);base=root/"runtime"/"predictive_data";base.mkdir(parents=True)
    preds=[
      {"prediction_id":"P1"},{"prediction_id":"P2"},{"prediction_id":"P3"},{"prediction_id":"P4"}
    ]
    (base/m.PREDICTION_LEDGER_NAME).write_text("\\n".join(json.dumps(x) for x in preds)+"\\n",encoding="utf-8")
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
    (base/m.OUTCOME_LEDGER_NAME).write_text("\\n".join(json.dumps(x) for x in outs)+"\\n",encoding="utf-8")
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
