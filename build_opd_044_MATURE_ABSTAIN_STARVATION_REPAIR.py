from pathlib import Path

ROOT=Path.cwd()
P=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_044_continuous_prospective_worker.py"
T=ROOT/"test_opd_044_MATURE_ABSTAIN_STARVATION_REPAIR.py"

s=P.read_text(encoding="utf-8")
old='def cycle(root=None,now=None,materializer=None,max_anchors=1,max_mature=4):\n root=Path(root or Path.cwd());intake=_intake_spool(root,max_anchors=max_anchors);rebuild_exact(root)\n all_rows=mature_exact(root,now);rows=all_rows[:max(0,int(max_mature))]\n resolved=0;abstained=0;fn=materializer or materialize_live\n for state in rows:\n  outcome=fn(state,root)\n  if outcome is None:abstained+=1;continue\n  resolve_exact(outcome,root);resolved+=1\n return {"intake_anchors":intake["anchors"],"intake_states":intake["states"],\n         "intake_backlog_remaining":intake["backlog_remaining"],\n         "mature_available":len(all_rows),"mature_processed":len(rows),\n         "resolved":resolved,"abstained":abstained}\n'
new='def cycle(root=None,now=None,materializer=None,max_anchors=1,max_mature=4,max_attempts=24):\n root=Path(root or Path.cwd());intake=_intake_spool(root,max_anchors=max_anchors);rebuild_exact(root)\n all_rows=mature_exact(root,now);target=max(0,int(max_mature));limit=max(target,int(max_attempts))\n resolved=0;abstained=0;attempted=0;fn=materializer or materialize_live\n for state in all_rows[:limit]:\n  if resolved>=target:break\n  attempted+=1;outcome=fn(state,root)\n  if outcome is None:abstained+=1;continue\n  resolve_exact(outcome,root);resolved+=1\n return {"intake_anchors":intake["anchors"],"intake_states":intake["states"],\n         "intake_backlog_remaining":intake["backlog_remaining"],\n         "mature_available":len(all_rows),"mature_processed":attempted,\n         "resolved":resolved,"abstained":abstained}\n'

if old not in s:
    raise SystemExit("REFUSE: expected repaired OPD-044 cycle boundary not found")

b=P.with_suffix(P.suffix+".pre_starvation_repair")
if not b.exists():
    b.write_bytes(P.read_bytes())

P.write_text(s.replace(old,new),encoding="utf-8")
T.write_text('from pathlib import Path\nimport tempfile\nimport qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker as w\n\nwith tempfile.TemporaryDirectory() as d:\n root=Path(d)\n w._intake_spool=lambda *a,**k:{"anchors":0,"states":0,"backlog_remaining":False}\n w.rebuild_exact=lambda *a,**k:None\n w.mature_exact=lambda *a,**k:[{"state_id":str(i)} for i in range(10)]\n seen=[]\n def mat(s,root):\n  seen.append(s["state_id"])\n  return None if int(s["state_id"])<4 else {"state_id":s["state_id"]}\n w.resolve_exact=lambda o,root:o\n z=w.cycle(root,materializer=mat,max_anchors=0,max_mature=2,max_attempts=8)\n assert seen==["0","1","2","3","4","5"],seen\n assert z["mature_processed"]==6 and z["abstained"]==4 and z["resolved"]==2,z\n\nprint("[PASS] mature abstainers no longer starve later resolvable states")\nprint("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")\n',encoding="utf-8")

compile(P.read_text(encoding="utf-8"),str(P),"exec")
compile(T.read_text(encoding="utf-8"),str(T),"exec")

print("[PASS] existing OPD-044 mature-abstain starvation repair installed")
print(P)
print(T)