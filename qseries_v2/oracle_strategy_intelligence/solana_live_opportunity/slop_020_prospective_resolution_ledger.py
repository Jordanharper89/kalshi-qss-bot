from dataclasses import asdict
from pathlib import Path
import json,os,tempfile
READ_ONLY=True;EXECUTION_AUTHORITY=False
REL=Path("runtime_state")/"solana_live_opportunity"/"economic_resolutions.json"
def _path(root=None):return Path(root or Path.cwd()).resolve()/REL
def _load(root=None):
 p=_path(root)
 if not p.exists():return {}
 raw=json.loads(p.read_text(encoding="utf-8"))
 return {str(x["prediction_id"]):dict(x) for x in tuple(raw.get("resolutions") or ())}
def persist_resolutions(resolutions,root=None):
 items=_load(root);new=existing=0
 for x in tuple(resolutions):
  d=asdict(x);pid=str(x.prediction_id)
  if pid in items:
   if items[pid]!=d:raise RuntimeError("immutable resolution collision: "+pid)
   existing+=1
  else:items[pid]=d;new+=1
 p=_path(root);p.parent.mkdir(parents=True,exist_ok=True)
 payload={"schema":"SLOP-020","read_only":True,"execution_authority":False,"resolutions":[items[k] for k in sorted(items)]}
 fd,tmp=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=str(p.parent))
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(payload,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 return {"total":len(items),"new":new,"existing":existing,"path":str(p),"execution_authority":False}
def read_resolution_dicts(root=None):return tuple(_load(root)[k] for k in sorted(_load(root)))
