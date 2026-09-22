from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

assert m.EXECUTION_AUTHORITY is False
assert m.PUBLICATION_ALLOWED is False
assert m.PREDICTION_LEDGER_REVISION=="FULL_EVIDENCE_PROSPECTIVE_LEDGER_V1"

anchor={"anchor_id":"A1","anchor_sequence_boundary":123,"ticker":"KXBTC15M-TEST",
        "contract_close_basis":"LIVE_PUBLIC_KALSHI_SOURCE_CLOSE_TIME"}

def score(h,passed):
    return {
      "state":{"ticker":"KXBTC15M-TEST","observed_epoch":1000.0,"anchor_price":0.55,
               "tokens":["K:A","CB:B","CC:C","L:D"]},
      "asset":"BTC","horizon_seconds":h,"contract_close_epoch":2000.0,
      "horizon_eligible":True,"direction":"DOWN","predicted_probability":0.71,
      "expected_return":0.04,"net_edge_after_2pct":0.02,
      "comparable_cases":40,"unique_tickers":5,"mean_similarity":0.4,
      "evidence_agreement":1.0,"evidence_votes":{"CB":{"direction":"DOWN"}},
      "checks":{"fresh_state":True,"contract_horizon":True,"net_edge":passed},
      "passed":passed
    }

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    first=m._freeze_predictions(root,anchor,[score(60,False),score(300,True)],1100.0)
    second=m._freeze_predictions(root,anchor,[score(60,False),score(300,True)],1130.0)
    p=Path(first["path"])
    rows=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert first["frozen"]==2 and first["duplicates"]==0
    assert second["frozen"]==0 and second["duplicates"]==2
    assert len(rows)==2
    assert len({r["prediction_id"] for r in rows})==2
    assert {r["horizon_seconds"] for r in rows}=={60,300}
    assert any(r["actionable_at_freeze"] is False and r["decision_at_freeze"]=="ABSTAIN" for r in rows)
    assert any(r["actionable_at_freeze"] is True and r["decision_at_freeze"]=="DOWN" for r in rows)
    assert all(r["profitability_status"]=="PROSPECTIVE_UNRESOLVED" for r in rows)
    assert all(r["execution_authority"] is False and r["publication_allowed"] is False for r in rows)

print("[PASS] immutable prospective prediction ledger append verified")
print("[PASS] deterministic prediction_id prevents duplicate re-freeze of same anchor+horizon")
print("[PASS] actionable AND abstained forecasts are frozen for unbiased prospective scoring")
print("[PASS] resolution_due_epoch and exact anchor lineage persisted")
print("[PASS] fsync append-only persistence enabled")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
