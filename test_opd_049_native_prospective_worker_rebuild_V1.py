import json,tempfile
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker import cycle,execution_authority
with tempfile.TemporaryDirectory() as d:
 r=Path(d);p=r/"runtime"/"predictive_data";p.mkdir(parents=True)
 row={"state_id":"S049","anchor_id":"A049","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":5,"tokens":[],"anchor_price":.50,"matched_family_ids":[],"post_freeze":True}
 (p/"opd_032_prospective_state_ledger.jsonl").write_text(json.dumps(row)+"\n")
 def mat(s,root):return {"state_id":s["state_id"],"resolution_epoch":105.0,"future_return":.06,"mfe":.06,"mae":-.03,"hit_plus_05":True,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False}
 x=cycle(r,105.0,mat);assert x=={"mature":1,"resolved":1,"abstained":0}
 out=json.loads((p/"opd_033_prospective_outcome_ledger.jsonl").read_text().splitlines()[0]);assert out["strictly_future"] is True and out["state_id"]=="S049"
 assert execution_authority is False
 print("[MATURE]",x["mature"],"[RESOLVED]",x["resolved"]);print("[STRICTLY_FUTURE]",out["strictly_future"]);print("[PASS] OPD-049 native worker rebuilt on certified 043/044/048 chain")
