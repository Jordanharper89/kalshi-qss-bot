import json,tempfile
from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker import cycle
with tempfile.TemporaryDirectory() as d:
 r=Path(d);p=r/"runtime"/"predictive_data";p.mkdir(parents=True)
 row={"state_id":"S053","anchor_id":"A053","ticker":"KXTEST","observed_epoch":100.0,"horizon_seconds":5,"tokens":[],"anchor_price":.50,"matched_family_ids":[],"post_freeze":True}
 (p/"opd_032_prospective_state_ledger.jsonl").write_text(json.dumps(row)+"\n")
 def mat(s,root):return {"state_id":"S053","resolution_epoch":105.0,"future_return":.04,"mfe":.06,"mae":-.01,"hit_plus_05":True,"hit_minus_05":False,"hit_plus_10":False,"hit_minus_10":False,"coverage_witness_epoch":106.0}
 x=cycle(r,105.0,mat);assert x["resolved"]==1
 out=json.loads((p/"opd_033_prospective_outcome_ledger.jsonl").read_text().splitlines()[0]);assert out["strictly_future"] is True
 print("[MATURE]",x["mature"],"[RESOLVED]",x["resolved"],"[ABSTAINED]",x["abstained"])
 print("[PASS] OPD-053 native worker rebuilt on witnessed future-outcome pavement")
