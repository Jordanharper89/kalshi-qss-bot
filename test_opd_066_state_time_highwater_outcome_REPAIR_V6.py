from pathlib import Path
import json
import qseries_v2.oracle_predictive_discovery.opd_056_highwater_witnessed_future_outcome as m
root=Path.cwd();rt=root/"runtime"/"predictive_data"

capt={}
m.state_time_highwater=lambda root,t:123
m.read_until_witness=lambda ticker,start,end,root,after:(capt.update({"after":after}) or ([{"event_epoch":106.0,"price":0.57}],106.0,140))
m.materialize_from_path_and_witness=lambda state,path,witness:{"state_id":state["state_id"],"resolution_epoch":witness}
r=m.materialize_live({"state_id":"x","ticker":"KXBTC-X","observed_epoch":100.0,"horizon_seconds":5},root)
assert capt["after"]==123 and r["coverage_start_sequence"]==123 and r["coverage_highwater_sequence"]==140

from qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker import cycle
sp=rt/"opd_061_live_anchor_spool.jsonl";st=rt/"opd_032_prospective_state_ledger.jsonl";ou=rt/"opd_033_prospective_outcome_ledger.jsonl"
def rows(p):return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
anchors={x["anchor_id"]:x for x in rows(sp)}
before={x["state_id"] for x in rows(ou)}
live5=[x for x in rows(st) if int(x.get("horizon_seconds",-1))==5 and x.get("anchor_id") in anchors and x["state_id"] not in before]
assert live5,"NO_UNRESOLVED_LIVE_5S_STATES"
import importlib
wm=importlib.reload(__import__("qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker",fromlist=["cycle"]))
result=wm.cycle(root)
after=rows(ou)
new=[x for x in after if x.get("state_id") not in before and x.get("strictly_future") is True]
live_ids={x["state_id"] for x in live5}
new5=[x for x in new if x.get("state_id") in live_ids]
print("[WORKER_CYCLE]",result)
print("[NEW_STRICTLY_FUTURE_OUTCOMES]",len(new))
print("[NEW_LIVE_5S_OUTCOMES]",len(new5))
assert new5,"HIGHWATER_REPAIR_RAN_BUT_NO_LIVE_5S_STATE_RESOLVED"
print("[STATE_ID]",new5[0]["state_id"],"[RESOLUTION_EPOCH]",new5[0]["resolution_epoch"])
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-066 highwater repair physically resolved live 5-second prospective state")
