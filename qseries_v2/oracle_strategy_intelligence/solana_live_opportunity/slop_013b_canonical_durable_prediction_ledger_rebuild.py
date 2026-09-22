from dataclasses import asdict
from pathlib import Path
import json,os,tempfile
from .slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity

READ_ONLY=True
EXECUTION_AUTHORITY=False
REL=Path("runtime_state")/"solana_live_opportunity"/"prospective_predictions.json"

def _path(root=None):
 return Path(root or Path.cwd()).resolve()/REL

def _canonical(x):
 d=asdict(x) if not isinstance(x,dict) else dict(x)
 d["conditions"]=[list(v) for v in tuple(d.get("conditions") or ())]
 return d

def _restore(d):
 x=dict(d)
 x["conditions"]=tuple(tuple(v) for v in tuple(x.get("conditions") or ()))
 return ProspectiveOpportunity(**x)

def _load(root=None):
 p=_path(root)
 if not p.exists(): return {}
 raw=json.loads(p.read_text(encoding="utf-8"))
 return {str(x["prediction_id"]):_canonical(x)
         for x in tuple(raw.get("predictions") or ())}

def _write(items,root=None):
 p=_path(root);p.parent.mkdir(parents=True,exist_ok=True)
 payload={"schema":"SLOP-013B","read_only":True,"execution_authority":False,
          "predictions":[items[k] for k in sorted(items)]}
 fd,tmp=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=str(p.parent))
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as f:
   json.dump(payload,f,indent=2,sort_keys=True)
   f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 return p

def persist_predictions(predictions,root=None):
 items=_load(root);new=existing=0
 for x in tuple(predictions):
  d=_canonical(x);pid=str(x.prediction_id)
  if pid in items:
   if items[pid]!=d:
    raise RuntimeError("immutable prediction collision: "+pid)
   existing+=1
  else:
   items[pid]=d;new+=1
 p=_write(items,root)
 return {"total":len(items),"new":new,"existing":existing,
         "path":str(p),"execution_authority":False}

def read_predictions(root=None,state=None):
 items=_load(root);out=[]
 for pid in sorted(items):
  x=_restore(items[pid])
  if state is not None and str(x.state)!=str(state):continue
  out.append(x)
 return tuple(out)
