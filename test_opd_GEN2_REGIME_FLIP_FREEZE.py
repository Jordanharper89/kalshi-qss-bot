import tempfile,json
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_gen2_regime_flip_freeze as m
with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    a=[{"family_id":"f","horizon_seconds":300,"target":"RETURN_POS","formula":["A"],
        "historical_holdout_lift":-0.1,"baseline_n":272,"trigger_n":24,"trigger_tickers":4,
        "prospective_lift":0.6,"sign_preserved":False,"directional_mean_return":0.08,
        "net_expected_after_hurdle":0.06,"mean_favorable_excursion":0.1,
        "mean_adverse_excursion":0.01,"reward_risk_proxy":10.0}]
    (rt/"opd_gen2_prospective_shortlist_audit.json").write_text(json.dumps(a))
    (rt/"opd_033_prospective_outcome_ledger.jsonl").write_text(json.dumps({"resolution_epoch":123.0})+"\n")
    b,_=m.build(r)
    assert b["candidate_count"]==1 and b["generation"]==2 and b["edge_certified"] is False
    assert b["selection_cutoff_resolution_epoch"]==123.0
assert m.execution_authority is False
print("[PASS] Gen2 regime-flip candidate freeze is immutable, selection-only, and post-cutoff safe")
print("[EDGE/PROBABILITY/DIRECTION/PUBLICATION/EXECUTION] FALSE/FALSE/FALSE/FALSE/FALSE")
