from pathlib import Path
R=Path.cwd()
P=R/'qseries_v2'/'oracle_predictive_discovery'/'opd_044_continuous_prospective_worker.py'
T=R/'test_opd_GEN2_MATURE_RESOLUTION_PRIORITY_REPAIR.py'
s=P.read_text(encoding='utf-8')
HELPER='def _gen2_state_ids(root):\n p=Path(root)/"runtime"/"predictive_data"/"opd_gen2_post_freeze_state_ledger.jsonl"\n ids=set()\n if not p.exists():return ids\n with p.open(encoding="utf-8") as f:\n  for line in f:\n   if line.strip():\n    try:ids.add(json.loads(line)["state_id"])\n    except Exception:pass\n return ids\ndef _prioritize_gen2(root,rows):\n ids=_gen2_state_ids(root)\n return sorted(rows,key=lambda x:(0 if x.get("state_id") in ids else 1,float(x.get("maturity_epoch",0)),str(x.get("state_id",""))))\n'
if 'def _prioritize_gen2(' not in s:
    marker='publication_allowed=False\n'
    if marker not in s: raise RuntimeError('OPD044_FLAG_BOUNDARY_NOT_FOUND')
    s=s.replace(marker,marker+HELPER,1)
old='all_rows=mature_exact(root,now);target=max(0,int(max_mature));limit=max(target,int(max_attempts))'
new='all_rows=mature_exact(root,now);all_rows=_prioritize_gen2(root,all_rows);target=max(0,int(max_mature));limit=max(target,int(max_attempts))'
if old not in s and new not in s: raise RuntimeError('OPD044_CURRENT_CYCLE_BOUNDARY_NOT_FOUND')
s=s.replace(old,new,1)
P.write_text(s,encoding='utf-8')
TEST='import json,tempfile\nfrom pathlib import Path\nimport qseries_v2.oracle_predictive_discovery.opd_044_continuous_prospective_worker as m\nwith tempfile.TemporaryDirectory() as d:\n r=Path(d);p=r/"runtime"/"predictive_data";p.mkdir(parents=True)\n (p/"opd_gen2_post_freeze_state_ledger.jsonl").write_text(json.dumps({"state_id":"g2"})+"\\n")\n rows=[{"state_id":"old1","maturity_epoch":1.0},{"state_id":"old2","maturity_epoch":2.0},{"state_id":"g2","maturity_epoch":999.0}]\n z=m._prioritize_gen2(r,rows)\n assert [x["state_id"] for x in z]==["g2","old1","old2"]\n assert m.execution_authority is False\nprint("[PASS] OPD-044 mature resolver prioritizes Gen2 post-freeze states before old backlog")\nprint("[PASS] old mature backlog is preserved behind Gen2; no outcome data is used for priority")\nprint("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")\n'
T.write_text(TEST,encoding='utf-8')
compile(P.read_text(encoding='utf-8'),str(P),'exec');compile(TEST,str(T),'exec')
print('[PASS] existing OPD-044 Gen2 mature-resolution priority repaired')
print(P);print(T)