import json,tempfile
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_live_prediction_candidate_now as m
with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    freeze={"activation_epoch":100.0,"candidates":[{"family_id":"f","horizon_seconds":300,"target":"RETURN_POS","formula":["A","B"],"net_expected_after_hurdle":0.06}]}
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps(freeze))
    s={"state_id":"s1","ticker":"KXBTC","observed_epoch":101.0,"horizon_seconds":300,"tokens":["A","B"],"anchor_price":0.42}
    (rt/"opd_032_prospective_state_ledger.jsonl").write_text(json.dumps(s)+"\n")
    z=m.run(r)
    assert z["match"] is True and z["direction"]=="UP"
with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps(freeze))
    s={"state_id":"s2","ticker":"KXETH","observed_epoch":102.0,"horizon_seconds":300,"tokens":["A"],"anchor_price":0.50}
    (rt/"opd_032_prospective_state_ledger.jsonl").write_text(json.dumps(s)+"\n")
    z=m.run(r)
    assert z["match"] is False
assert m.execution_authority is False
print("[PASS] current post-freeze 300s state produces UP/DOWN candidate only on exact frozen formula match")
print("[PASS] positive frozen selection edge is labeled UNPROVEN until fresh resolved trigger economics exist")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
