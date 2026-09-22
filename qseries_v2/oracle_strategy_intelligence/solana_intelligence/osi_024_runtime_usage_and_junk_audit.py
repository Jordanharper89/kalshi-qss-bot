from __future__ import annotations
import json,time
from pathlib import Path

def audit(root:Path)->dict:
 now=time.time(); rows=[]
 for base_name in ("runtime","runtime_state"):
  base=root/base_name
  if not base.exists(): continue
  for p in base.rglob("*"):
   if not p.is_file(): continue
   s=p.stat(); age=max(0,now-s.st_mtime)
   rows.append({"path":str(p.relative_to(root)),"size":s.st_size,"age_seconds":age,"suffix":p.suffix.lower()})
 rows.sort(key=lambda x:x["size"],reverse=True)
 total=sum(x["size"] for x in rows)
 return {"revision":"OSI_024","file_count":len(rows),"total_bytes":total,
         "largest_files":rows[:100],
         "over_1gb":[x for x in rows if x["size"]>=1_000_000_000],
         "over_100mb":[x for x in rows if x["size"]>=100_000_000],
         "older_than_7d":[x for x in rows if x["age_seconds"]>=604800][:250],
         "execution_authority":False,"read_only":True,
         "scope":"inventory_only_no_delete"}

def write_report(root:Path)->Path:
 p=root/"OSI_024_RUNTIME_USAGE_AND_JUNK_AUDIT.json"
 p.write_text(json.dumps(audit(root),indent=2,sort_keys=True),encoding="utf-8")
 return p
