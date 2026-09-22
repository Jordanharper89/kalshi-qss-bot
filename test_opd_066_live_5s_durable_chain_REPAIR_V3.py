from pathlib import Path
import json
root=Path.cwd();rt=root/"runtime"/"predictive_data"
spool=rt/"opd_061_live_anchor_spool.jsonl"
states=rt/"opd_032_prospective_state_ledger.jsonl"
outs=rt/"opd_033_prospective_outcome_ledger.jsonl"
cursor=rt/"opd_065_intake_cursor.json"
hb=rt/"opd_065_worker_heartbeat.json"
def rows(p): return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
assert spool.exists() and spool.stat().st_size>0,"NO_OPD061_LIVE_ANCHORS"
a=rows(spool);s=rows(states) if states.exists() else [];o=rows(outs) if outs.exists() else []
anchors={x.get("anchor_id"):x for x in a}
five=[x for x in s if int(x.get("horizon_seconds",-1))==5 and x.get("post_freeze") is True and x.get("anchor_id") in anchors]
assert five,"NO_OPD061_ANCHOR_REACHED_OPD032_5S_STATE"
resolved_by={x.get("state_id"):x for x in o if x.get("strictly_future") is True}
pairs=[(x,resolved_by.get(x.get("state_id"))) for x in five if x.get("state_id") in resolved_by]
assert pairs,"NO_LIVE_5S_STATE_HAS_STRICTLY_FUTURE_OPD033_OUTCOME"
state,outcome=pairs[-1];anchor=anchors[state["anchor_id"]]
assert float(outcome["resolution_epoch"])>=float(state["observed_epoch"])+5,"FUTURE_HORIZON_VIOLATION"
assert abs(float(anchor["observed_epoch"])-float(state["observed_epoch"]))<1e-9,"ANCHOR_STATE_TIME_MISMATCH"
c=json.loads(cursor.read_text(encoding="utf-8")) if cursor.exists() else {}
h=json.loads(hb.read_text(encoding="utf-8")) if hb.exists() else {}
assert int(c.get("byte_offset",0))>0,"OPD065_CURSOR_NOT_ADVANCING"
assert h.get("state")=="HEALTHY","OPD065_WORKER_NOT_HEALTHY"
print("[LIVE_ANCHORS]",len(a),"[SPOOL_BYTES]",spool.stat().st_size)
print("[LIVE_5S_STATES]",len(five),"[STRICTLY_FUTURE_5S_RESOLVED]",len(pairs))
print("[ANCHOR]",anchor["ticker"],anchor["anchor_id"],anchor["observed_epoch"])
print("[STATE_ID]",state["state_id"],"[HORIZON]",state["horizon_seconds"])
print("[RESOLUTION_EPOCH]",outcome["resolution_epoch"],"[STRICTLY_FUTURE]",outcome["strictly_future"])
print("[CURSOR_BYTE_OFFSET]",c.get("byte_offset"),"[WORKER]",h.get("state"),h.get("result"))
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
print("[PASS] OPD-066 live prospective 5-second chain physically certified from durable production evidence")
