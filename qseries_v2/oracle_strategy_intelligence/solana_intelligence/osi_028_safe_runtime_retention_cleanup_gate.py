from __future__ import annotations
import json,time
from pathlib import Path
PROTECTED=("continuity","recovery","settlement","learning","outcome","state","queue","manifest","registry")
TRANSIENT=("debug","tmp","temp","trace","spool","raw_events")
def plan(root:Path)->dict:
 now=time.time();items=[]
 for base_name in ("runtime","runtime_state"):
  base=root/base_name
  if not base.exists():continue
  for p in base.rglob("*"):
   if not p.is_file():continue
   s=p.stat();rel=str(p.relative_to(root));low=rel.lower();age=max(0,now-s.st_mtime)
   if any(k in low for k in PROTECTED):
    action="KEEP_PROTECTED"
   elif s.st_size>=1_000_000_000 and any(k in low for k in TRANSIENT):
    action="ROTATE_OR_ARCHIVE_REVIEW"
   elif age>=2_592_000 and any(k in low for k in TRANSIENT):
    action="RETIRE_REVIEW"
   elif s.st_size>=250_000_000:
    action="REVIEW_LARGE"
   else:
    action="KEEP"
   items.append({"path":rel,"size":s.st_size,"age_seconds":age,"proposed_action":action})
 counts={}
 for x in items:counts[x["proposed_action"]]=counts.get(x["proposed_action"],0)+1
 return {"revision":"OSI_028","items":items,"counts":counts,
  "destructive_action_authorized":False,"execution_authority":False,"read_only":True,
  "rule":"No deletion until an explicit later retirement build consumes this reviewed plan."}
def write_plan(root:Path)->Path:
 p=root/"OSI_028_SAFE_RUNTIME_RETENTION_CLEANUP_PLAN.json";p.write_text(json.dumps(plan(root),indent=2,sort_keys=True),encoding="utf-8");return p
