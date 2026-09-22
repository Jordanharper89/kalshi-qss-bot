from pathlib import Path
import tempfile,json,importlib
import qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker as w

with tempfile.TemporaryDirectory() as d:
 root=Path(d);rt=root/"runtime"/"predictive_data";rt.mkdir(parents=True)
 rows=[{"anchor_id":f"a{i}","ticker":"KXBTC","observed_epoch":100+i,"anchor_price":.5,"kalshi_state":{}} for i in range(3)]
 (rt/"opd_061_live_anchor_spool.jsonl").write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
 calls=[]
 w.intake_anchor=lambda a,*args,**kwargs:calls.append(a["anchor_id"]) or [None]*7
 a=w._intake_spool(root,max_anchors=1)
 assert a["anchors"]==1 and a["states"]==7 and a["backlog_remaining"] is True and calls==["a0"]
 c1=json.loads((rt/"opd_065_intake_cursor.json").read_text())["byte_offset"]
 a=w._intake_spool(root,max_anchors=1)
 c2=json.loads((rt/"opd_065_intake_cursor.json").read_text())["byte_offset"]
 assert a["anchors"]==1 and calls==["a0","a1"] and c2>c1
 w.rebuild_exact=lambda root:None
 w.mature_exact=lambda root,now=None:[{"state_id":str(i)} for i in range(9)]
 w.materialize_live=lambda s,root:{"state_id":s["state_id"]}
 w.resolve_exact=lambda o,root:o
 w._intake_spool=lambda root,max_anchors=1:{"anchors":0,"states":0,"backlog_remaining":False}
 z=w.cycle(root,max_anchors=0,max_mature=4)
 assert z["mature_available"]==9 and z["mature_processed"]==4 and z["resolved"]==4
print("[PASS] existing worker bounded intake + per-anchor durable cursor + bounded maturity progress")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
