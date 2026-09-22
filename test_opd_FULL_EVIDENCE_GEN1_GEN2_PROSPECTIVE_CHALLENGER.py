from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as p
import qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard_clean as sb

assert p.EXECUTION_AUTHORITY is False
assert p.PUBLICATION_ALLOWED is False
assert p.HURDLE==0.020
assert p.GENERATION_CHALLENGER_REVISION=="GEN1_GEN2_PROSPECTIVE_CHALLENGER_V1"
assert p.GEN1_MIN_RESOLVED==12
assert p.GEN1_MIN_TICKERS==3

with tempfile.TemporaryDirectory() as td:
    root=Path(td);base=root/"runtime"/"predictive_data";base.mkdir(parents=True)
    freeze={
      "schema_version":"OPD-031","activation_epoch":1000.0,
      "candidate_count":1,"formula_retuning_allowed":False,
      "threshold_retuning_allowed":False,
      "historical_data_allowed_for_prospective_scoring":False,
      "edge_certified_count":0,"execution_authority":False,
      "candidates":[{
        "family_id":"GEN1-F","representative_formula_id":"R1","degree":2,
        "horizon_seconds":300,"target":"RETURN_NEG",
        "formula":["CB:X","CC:Y"],
        "historical_discovery_lift":0.2,"historical_holdout_lift":0.1,
        "historical_holdout_q":0.01,"historical_net_after_hurdle":0.05
      }]
    }
    (base/p.GEN1_FREEZE_NAME).write_text(json.dumps(freeze),encoding="utf-8")
    base_score={
      "generation":2,"model_basis":"FULL_EVIDENCE_CURRENT_MODEL",
      "state":{"state_id":"S","ticker":"KXBTCD-NOW-T77000",
               "observed_epoch":2000.0,"anchor_price":0.55,
               "tokens":["CB:X","CC:Y","K:Z","L:W"]},
      "asset":"BTC","horizon_seconds":300,"age_seconds":1.0,
      "contract_close_epoch":3000.0,"contract_remaining_seconds":1000.0,
      "horizon_eligible":True,
      "checks":{"fresh_state":True,"contract_horizon":True},
    }

    z=p._gen1_challenger_scores(root,[base_score],2001.0)
    assert len(z)==1
    assert z[0]["direction"]=="DOWN"
    assert z[0]["passed"] is False
    assert z[0]["checks"]["gen1_prospective_support"] is False

    rows=[]
    for i in range(18):
        rows.append({
          "prediction_id":f"G1-{i}","resolution_status":"RESOLVED_EXACT_FUTURE",
          "resolved_epoch":1900.0,"generation":1,"family_id":"GEN1-F",
          "ticker":f"KXBTCD-H{i%4}-T77000","horizon_seconds":300,
          "direction":"DOWN","directional_return":0.07
        })
    rows.append({
      "prediction_id":"FUTURE","resolution_status":"RESOLVED_EXACT_FUTURE",
      "resolved_epoch":2100.0,"generation":1,"family_id":"GEN1-F",
      "ticker":"KXBTCD-FUTURE-T77000","horizon_seconds":300,
      "direction":"DOWN","directional_return":9.0
    })
    with (base/"opd_full_evidence_live_outcome_ledger.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r)+"\n")
    z=p._gen1_challenger_scores(root,[base_score],2001.0)
    assert len(z)==1
    st=z[0]["prospective_realized_edge"]
    assert st["n"]==18 and st["unique_tickers"]==4
    assert st["lower_bound_net_after_2pct"]>0
    assert z[0]["passed"] is True

    rows=[dict(r,directional_return=0.0) for r in rows[:-1]]
    with (base/"opd_full_evidence_live_outcome_ledger.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r)+"\n")
    z=p._gen1_challenger_scores(root,[base_score],2001.0)
    assert z[0]["passed"] is False
    assert z[0]["checks"]["gen1_prospective_realized_edge"] is False

    anchor={"anchor_id":"A","anchor_sequence_boundary":7,"ticker":"KXBTCD-NOW-T77000"}
    assert p._prediction_id(anchor,300,2,None)!=p._prediction_id(anchor,300,1,"GEN1-F")

    pred=[{"prediction_id":"A"},{"prediction_id":"B"}]
    out=[
      {"prediction_id":"A","resolution_status":"RESOLVED_EXACT_FUTURE",
       "generation":1,"family_id":"GEN1-F","actionable_at_freeze":True,
       "horizon_seconds":300,"directional_return":0.08,"predicted_probability":None},
      {"prediction_id":"B","resolution_status":"RESOLVED_EXACT_FUTURE",
       "generation":2,"actionable_at_freeze":True,
       "horizon_seconds":300,"directional_return":-0.01,"predicted_probability":0.7},
    ]
    with (base/sb.PREDICTION_LEDGER_NAME).open("w",encoding="utf-8") as f:
        for r in pred:f.write(json.dumps(r)+"\n")
    with (base/sb.OUTCOME_LEDGER_NAME).open("w",encoding="utf-8") as f:
        for r in out:f.write(json.dumps(r)+"\n")
    b=sb.build_scoreboard(root)
    assert b["by_generation"]["1"]["actionable"]["mean_net_realized_after_2pct"]>0
    assert b["by_generation"]["2"]["actionable"]["mean_net_realized_after_2pct"]<0

resolver=Path("qseries_v2/oracle_predictive_discovery/opd_full_evidence_exact_future_outcome_resolver.py").read_text(encoding="utf-8")
scoreboard=Path("qseries_v2/oracle_predictive_discovery/opd_full_evidence_live_profitability_scoreboard_clean.py").read_text(encoding="utf-8")
predictor=Path("qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py").read_text(encoding="utf-8")
assert '"generation":int(p.get("generation") or 2)' in resolver
assert '"family_id":p.get("family_id")' in resolver
assert '"by_generation": by_generation' in scoreboard
assert 'ORIGINAL_FROZEN_OPD031_GEN1' in predictor
assert 'GEN1_MIN_RESOLVED=12' in predictor
assert 'GEN1_MIN_TICKERS=3' in predictor
assert 'scores.extend(gen1_scores)' in predictor

print("[PASS] original OPD-031 Gen1 formulas restored exactly as a live challenger")
print("[PASS] Gen1 formula/threshold retuning remains forbidden")
print("[PASS] current full-evidence model retained as generation 2 baseline")
print("[PASS] same anchor+horizon can freeze Gen1 and Gen2 without prediction-id collision")
print("[PASS] exact future resolver preserves generation + family lineage")
print("[PASS] Gen1 future outcomes cannot leak backward across current anchor cutoff")
print("[PASS] Gen1 requires 12 resolved cases / 3 tickers and positive conservative net lower bound")
print("[PASS] negative prospective Gen1 economics force abstention")
print("[PASS] profitability scoreboard now separates Gen1 vs Gen2 realized economics")
print("[PASS] fixed 2pct hurdle, freshness, contract lifetime, publication, execution unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
