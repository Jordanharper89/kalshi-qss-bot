import tempfile,json
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_gen2_fresh_evidence_status as m
with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps({
        "generation":2,"activation_epoch":100.0,
        "candidates":[{"family_id":"f","horizon_seconds":300,"target":"RETURN_POS"}]}))
    s={"state_id":"s","ticker":"KXBTC","horizon_seconds":300,"matched_family_ids":["f"]}
    (rt/"opd_gen2_post_freeze_state_ledger.jsonl").write_text(json.dumps(s)+"\n")
    o={"state_id":"s","future_return":0.08,"mfe":0.10,"mae":-0.02}
    (rt/"opd_033_prospective_outcome_ledger.jsonl").write_text(json.dumps(o)+"\n")
    x=m.status(r)[0]
    assert x["resolved_baseline_n"]==1 and x["resolved_trigger_n"]==1
    assert abs(x["net_expected_after_hurdle"]-0.06)<1e-9
    assert x["edge_certified"] is False
assert m.execution_authority is False
print("[PASS] Gen2 fresh evidence status uses only post-freeze states and resolved outcomes")
print("[EDGE/PROBABILITY/DIRECTION/PUBLICATION/EXECUTION] FALSE/FALSE/FALSE/FALSE/FALSE")
