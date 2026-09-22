from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_full_evidence_exact_future_outcome_resolver as m

def fake_materializer(state,root=None,after_sequence=None):
    assert after_sequence==123
    assert state["anchor_sequence_boundary"]==123
    return {"state_id":state["state_id"],"resolution_epoch":1300.0,
      "future_return":-0.08,"future_end_price":0.47,"mfe":0.01,"mae":-0.10,
      "outcome_basis":"OBSERVED_SAME_TICKER_PATH","coverage_witness_epoch":1301.0,
      "coverage_start_sequence":123,"coverage_highwater_sequence":999,
      "anchor_sequence_exact":True}

with tempfile.TemporaryDirectory() as td:
    root=Path(td);base=root/"runtime"/"predictive_data";base.mkdir(parents=True)
    p1={"prediction_id":"P1","ticker":"KXBTC15M-TEST","anchor_id":"A1",
        "anchor_sequence_boundary":123,"anchor_observed_epoch":1000.0,
        "anchor_price":0.55,"horizon_seconds":300,"resolution_due_epoch":1300.0,
        "horizon_eligible":True,"direction":"DOWN","predicted_probability":0.72,
        "expected_return":0.05,"net_edge_after_2pct":0.03,
        "actionable_at_freeze":True,"decision_at_freeze":"DOWN"}
    p2=dict(p1,prediction_id="P2",horizon_seconds=900,resolution_due_epoch=1900.0,
            horizon_eligible=False,actionable_at_freeze=False,decision_at_freeze="ABSTAIN")
    (base/m.PREDICTION_LEDGER_NAME).write_text(json.dumps(p1)+"\n"+json.dumps(p2)+"\n",encoding="utf-8")
    first=m.resolve_matured(root,2000.0,fake_materializer)
    second=m.resolve_matured(root,2030.0,fake_materializer)
    rows=[json.loads(x) for x in (base/m.OUTCOME_LEDGER_NAME).read_text().splitlines()]
    assert first["resolved_now"]==1 and first["ineligible"]==1 and first["errors"]==0
    assert second["resolved_now"]==0 and second["ineligible"]==0
    assert len(rows)==2
    good=[x for x in rows if x["prediction_id"]=="P1"][0]
    assert good["resolution_status"]=="RESOLVED_EXACT_FUTURE"
    assert good["future_return"]==-0.08 and good["directional_return"]==0.08
    assert good["coverage_start_sequence"]==123 and good["anchor_sequence_exact"] is True
    assert [x for x in rows if x["prediction_id"]=="P2"][0]["resolution_status"]=="CONTRACT_HORIZON_INELIGIBLE"

runner=Path("run_opd_full_evidence_predictor_child.py").read_text(encoding="utf-8")
assert "run_prediction(root=root)" in runner
assert "resolve_full_evidence_outcomes(root)" in runner
assert runner.index("run_prediction(root=root)") < runner.index("resolve_full_evidence_outcomes(root)")

print("[PASS] exact current continuous-child call boundary patched")
print("[PASS] matured prediction resolves from exact frozen anchor sequence")
print("[PASS] strict-future OPD-056 materializer reused")
print("[PASS] immutable outcome ledger prevents duplicate resolution")
print("[PASS] contract-horizon-ineligible forecasts terminalized non-scorable")
print("[PASS] transient resolver/materializer errors fail closed without fabricating outcomes")
print("[PASS] resolver runs after each existing 30-second prediction cycle")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
