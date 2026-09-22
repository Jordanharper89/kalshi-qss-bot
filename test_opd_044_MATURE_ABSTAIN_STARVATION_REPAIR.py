from pathlib import Path
import tempfile
import qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker as w

with tempfile.TemporaryDirectory() as d:
 root=Path(d)
 w._intake_spool=lambda *a,**k:{"anchors":0,"states":0,"backlog_remaining":False}
 w.rebuild_exact=lambda *a,**k:None
 w.mature_exact=lambda *a,**k:[{"state_id":str(i)} for i in range(10)]
 seen=[]
 def mat(s,root):
  seen.append(s["state_id"])
  return None if int(s["state_id"])<4 else {"state_id":s["state_id"]}
 w.resolve_exact=lambda o,root:o
 z=w.cycle(root,materializer=mat,max_anchors=0,max_mature=2,max_attempts=8)
 assert seen==["0","1","2","3","4","5"],seen
 assert z["mature_processed"]==6 and z["abstained"]==4 and z["resolved"]==2,z

print("[PASS] mature abstainers no longer starve later resolvable states")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
