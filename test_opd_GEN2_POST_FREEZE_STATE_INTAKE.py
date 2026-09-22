import json,tempfile
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_gen2_post_freeze_state_intake as m

with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    freeze={
        "generation":2,
        "activation_epoch":100.0,
        "candidate_count":1,
        "candidates":[{"family_id":"f","horizon_seconds":300,"formula":["A","B"]}]
    }
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps(freeze))
    rows=[
        {"state_id":"old","anchor_id":"a0","ticker":"OLD","observed_epoch":99.0,
         "horizon_seconds":300,"tokens":["A","B"],"anchor_price":0.5},
        {"state_id":"base","anchor_id":"a1","ticker":"BASE","observed_epoch":101.0,
         "horizon_seconds":300,"tokens":["A"],"anchor_price":0.5},
        {"state_id":"hit","anchor_id":"a2","ticker":"HIT","observed_epoch":102.0,
         "horizon_seconds":300,"tokens":["A","B"],"anchor_price":0.5},
        {"state_id":"wrongh","anchor_id":"a3","ticker":"H5","observed_epoch":103.0,
         "horizon_seconds":5,"tokens":["A","B"],"anchor_price":0.5},
    ]
    (rt/"opd_032_prospective_state_ledger.jsonl").write_text(
        "".join(json.dumps(x)+"\n" for x in rows))
    s=m.ingest(r)
    assert s["gen2_states_total"]==2
    assert s["gen2_trigger_states_total"]==1
    assert s["pre_freeze_rejected_this_run"]==1
    assert s["wrong_horizon_this_run"]==1
    assert s["all_post_gen2_freeze"] is True
    assert s["selection_reused"] is False
    s2=m.ingest(r)
    assert s2["gen2_states_total"]==2

assert m.execution_authority is False
print("[PASS] Gen2 state intake accepts only truly post-freeze candidate-horizon states")
print("[PASS] baseline + trigger evidence are isolated from the 323 selection rows")
print("[EDGE/PROBABILITY/DIRECTION/PUBLICATION/EXECUTION] FALSE/FALSE/FALSE/FALSE/FALSE")
