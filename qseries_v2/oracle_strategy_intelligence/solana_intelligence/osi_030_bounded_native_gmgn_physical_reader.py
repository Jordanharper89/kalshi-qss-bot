from __future__ import annotations
import json
from pathlib import Path
ENDPOINTS="runtime_state/solana_opportunities/physical_source_endpoints.json"
def _read(path:Path,limit:int=100)->list[dict]:
 out=[]
 try:
  if path.suffix.lower()==".json":
   obj=json.loads(path.read_text(encoding="utf-8",errors="replace"));vals=obj if isinstance(obj,list) else [obj]
   return [x for x in vals[-limit:] if isinstance(x,dict)]
  if path.suffix.lower()==".jsonl":
   lines=path.read_text(encoding="utf-8",errors="replace").splitlines()[-limit:]
   for line in lines:
    try:
     x=json.loads(line)
     if isinstance(x,dict):out.append(x)
    except Exception:pass
 except Exception:pass
 return out
def read_registered(root:Path,limit_per_file:int=100,max_files:int=20)->dict:
 ep=root/ENDPOINTS
 if not ep.is_file():raise RuntimeError("Missing OSI-029 endpoint registry")
 d=json.loads(ep.read_text(encoding="utf-8"))
 native=[];gmgn=[]
 for rel in d.get("physical_native_files",[])[:max_files]:
  for row in _read(root/rel,limit_per_file):native.append({"source":rel,"row":row})
 for rel in d.get("physical_gmgn_files",[])[:max_files]:
  for row in _read(root/rel,limit_per_file):gmgn.append({"source":rel,"row":row})
 return {"native":native,"gmgn":gmgn,"native_rows":len(native),"gmgn_rows":len(gmgn),
  "execution_authority":False,"read_only":True,"bounded":True}
