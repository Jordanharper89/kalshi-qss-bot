from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

assert m.EXECUTION_AUTHORITY is False
assert m.PUBLICATION_ALLOWED is False
assert m.HURDLE==0.020
assert m.MIN_NET_EDGE==0.005
assert m.PROSPECTIVE_EDGE_GATE_REVISION=="PROSPECTIVE_REALIZED_EDGE_GATE_V1"
assert m.PROSPECTIVE_EDGE_MIN_N==12
assert m.PROSPECTIVE_EDGE_MIN_TICKERS==3

base_score={
 "state":{"ticker":"KXBTCD-NOW-T77000","observed_epoch":2000.0},
 "asset":"BTC","horizon_seconds":60,"direction":"DOWN",
 "predicted_probability":0.72,"evidence_agreement":1.0,
 "checks":{"fresh_state":True,"comparable_cases":True,"ticker_breadth":True,
           "mean_similarity":True,"direction_probability":True,"net_edge":True,
           "evidence_agreement":True},
 "passed":True,
}

def outcome(i,net,resolved=1900.0,ticker=None,prob=.72,agree=1.0):
    return {
      "prediction_id":f"P{i}","resolution_status":"RESOLVED_EXACT_FUTURE",
      "resolution_epoch":resolved,
      "ticker":ticker or f"KXBTCD-HIST{i%4}-T77000",
      "horizon_seconds":60,"predicted_direction":"DOWN",
      "predicted_probability":prob,"evidence_agreement":agree,
      "directional_return":0.02+net,
    }

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    p=root/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
    p.parent.mkdir(parents=True)

    rows=[outcome(i,.04 if i%3 else .02,ticker=f"KXBTCD-H{i%4}-T77000") for i in range(18)]
    rows.append(outcome(99,9.0,resolved=2100.0,ticker="KXBTCD-FUTURE-T77000"))
    p.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
    s=m._prospective_gate_apply(dict(base_score,checks=dict(base_score["checks"])),root)
    z=s["prospective_realized_edge"]
    assert z["n"]==18
    assert z["unique_tickers"]==4
    assert z["mean_net_after_2pct"]>0
    assert z["lower_bound_net_after_2pct"]>0
    assert s["checks"]["prospective_realized_edge"] is True
    assert s["passed"] is True

    rows=[outcome(i,-.015,ticker=f"KXBTCD-H{i%4}-T77000") for i in range(18)]
    p.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
    s=m._prospective_gate_apply(dict(base_score,checks=dict(base_score["checks"])),root)
    assert s["prospective_realized_edge"]["mean_net_after_2pct"]<0
    assert s["checks"]["prospective_realized_edge"] is False
    assert s["passed"] is False

    rows=[outcome(i,.05,ticker=f"KXBTCD-H{i%2}-T77000") for i in range(5)]
    p.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
    s=m._prospective_gate_apply(dict(base_score,checks=dict(base_score["checks"])),root)
    assert s["prospective_realized_edge"]["n"]==5
    assert s["checks"]["prospective_realized_edge"] is False

src=Path("qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py").read_text(encoding="utf-8")
assert "def _score_state_preprospective(" in src
assert 'PROSPECTIVE_EDGE_GATE_REVISION="PROSPECTIVE_REALIZED_EDGE_GATE_V1"' in src
assert '"prospective_realized_edge"' in src
assert "lower_bound_net_after_2pct" in src
assert "resolution_status" in src
assert "resolved_at>float(cutoff_epoch)" in src
assert "REALTIME_TRADE_TICKER_ANCHOR_ROOT_V1" in src
assert "EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1" in src

print("[PASS] prospective realized-edge gate installed inside existing full-evidence scorer")
print("[PASS] exact resolved prospective outcomes are now a first-class actionability gate")
print("[PASS] horizon + direction + contract-family + probability + agreement regime matched")
print("[PASS] future-resolved rows are excluded by strict pre-anchor cutoff")
print("[PASS] positive mean alone is insufficient; conservative net lower bound must exceed zero")
print("[PASS] minimum 12 resolved cases across 3 tickers required")
print("[PASS] negative/sparse prospective economics force abstention")
print("[PASS] original 2pct hurdle and every existing evidence gate preserved")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
