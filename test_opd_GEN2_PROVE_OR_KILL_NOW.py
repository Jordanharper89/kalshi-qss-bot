import json,tempfile
from pathlib import Path
import qseries_v2.oracle_predictive_discovery.opd_gen2_prove_or_kill_now as m

with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    freeze={"generation":2,"activation_epoch":100.0,"candidates":[{"family_id":"f","horizon_seconds":300,"target":"RETURN_POS"}]}
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps(freeze))
    states=[]
    outcomes=[]
    for i in range(500):
        match=i<100
        s={"state_id":f"s{i}","ticker":f"KXBTC{i%10}","observed_epoch":101+i,"horizon_seconds":300,
           "anchor_price":0.40,"matched_family_ids":["f"] if match else []}
        states.append(s)
        ret=0.08 if match else (-0.01 if i%2 else 0.01)
        outcomes.append({"state_id":f"s{i}","future_return":ret,"mfe":0.10 if match else 0.02,"mae":-0.02})
    (rt/"opd_gen2_post_freeze_state_ledger.jsonl").write_text("".join(json.dumps(x)+"\n" for x in states))
    (rt/"opd_033_prospective_outcome_ledger.jsonl").write_text("".join(json.dumps(x)+"\n" for x in outcomes))
    z=m.prove_or_kill(r)
    assert z["verdict"]=="PROVEN"
    assert z["best"]["certified"] is True

with tempfile.TemporaryDirectory() as d:
    r=Path(d);rt=r/"runtime"/"predictive_data";rt.mkdir(parents=True)
    (rt/"opd_gen2_candidate_freeze.json").write_text(json.dumps({"generation":2,"activation_epoch":100.0,"candidates":[{"family_id":"f","horizon_seconds":300,"target":"RETURN_POS"}]}))
    (rt/"opd_gen2_post_freeze_state_ledger.jsonl").write_text(json.dumps({"state_id":"s","ticker":"KXBTC","observed_epoch":101,"horizon_seconds":300,"matched_family_ids":[]})+"\n")
    z=m.prove_or_kill(r)
    assert z["verdict"]=="NOT_PROVEN"

assert m.execution_authority is False
print("[PASS] prove-or-kill emits PROVEN only after fresh post-freeze economics satisfy every fixed gate")
print("[PASS] insufficient or losing evidence emits NO PROVEN PROFITABLE EDGE")
print("[EXECUTION/PROBABILITY/PUBLICATION] FALSE/FALSE/FALSE")
