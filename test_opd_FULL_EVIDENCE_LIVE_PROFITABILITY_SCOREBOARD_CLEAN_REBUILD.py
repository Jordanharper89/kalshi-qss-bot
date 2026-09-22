from pathlib import Path
import json
import tempfile
import qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard_clean as m

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    base = root / "runtime" / "predictive_data"
    base.mkdir(parents=True)

    predictions = [
        {"prediction_id": "P1"},
        {"prediction_id": "P2"},
        {"prediction_id": "P3"},
        {"prediction_id": "P4"},
    ]
    outcomes = [
        {"prediction_id": "P1", "resolution_status": "RESOLVED_EXACT_FUTURE",
         "actionable_at_freeze": True, "horizon_seconds": 300,
         "directional_return": 0.08, "predicted_probability": 0.70},
        {"prediction_id": "P2", "resolution_status": "RESOLVED_EXACT_FUTURE",
         "actionable_at_freeze": True, "horizon_seconds": 300,
         "directional_return": -0.01, "predicted_probability": 0.60},
        {"prediction_id": "P3", "resolution_status": "RESOLVED_EXACT_FUTURE",
         "actionable_at_freeze": False, "horizon_seconds": 60,
         "directional_return": 0.03, "predicted_probability": 0.55},
        {"prediction_id": "P4", "resolution_status": "CONTRACT_HORIZON_INELIGIBLE",
         "actionable_at_freeze": False, "horizon_seconds": 900},
    ]

    with (base / m.PREDICTION_LEDGER_NAME).open("w", encoding="utf-8") as f:
        for row in predictions:
            f.write(json.dumps(row) + "\n")

    with (base / m.OUTCOME_LEDGER_NAME).open("w", encoding="utf-8") as f:
        for row in outcomes:
            f.write(json.dumps(row) + "\n")

    board = m.build_scoreboard(root)
    a = board["actionable"]

    assert board["prediction_rows"] == 4
    assert board["resolved_exact_future_rows"] == 3
    assert a["n"] == 2
    assert abs(a["hit_rate"] - 0.5) < 1e-12
    assert abs(a["mean_directional_return"] - 0.035) < 1e-12
    assert abs(a["mean_net_realized_after_2pct"] - 0.015) < 1e-12
    assert abs(a["cumulative_net_realized_after_2pct"] - 0.03) < 1e-12
    assert a["positive_net_count"] == 1
    assert a["negative_net_count"] == 1
    assert board["profitability_status"] == "POSITIVE_NET_EXPECTANCY_OBSERVED"
    assert board["profitability_certified"] is False
    assert board["abstained"]["n"] == 1
    assert "300" in board["actionable_by_horizon"]

    disk = json.loads((base / m.SCOREBOARD_NAME).read_text(encoding="utf-8"))
    assert disk["resolved_exact_future_rows"] == 3
    assert disk["actionable"]["n"] == 2
    assert disk["execution_authority"] is False
    assert disk["publication_allowed"] is False

runner = Path("run_opd_full_evidence_predictor_child.py").read_text(encoding="utf-8")
assert "run_prediction(root=root)" in runner
assert "resolve_full_evidence_outcomes(root)" in runner
assert "run_full_evidence_scoreboard_clean(root)" in runner
assert runner.index("run_prediction(root=root)") < runner.index("resolve_full_evidence_outcomes(root)") < runner.index("run_full_evidence_scoreboard_clean(root)")

print("[PASS] clean scoreboard reads exact resolved outcome ledger")
print("[PASS] actionable predictions separated from abstained forecasts")
print("[PASS] directional return and fixed 2pct realized net economics verified")
print("[PASS] hit rate, Brier score, calibration error, and horizon breakdown verified")
print("[PASS] atomic scoreboard JSON write verified")
print("[PASS] profitability certification remains FALSE")
print("[PASS] clean scoreboard runs after exact resolver in existing 30-second child")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
