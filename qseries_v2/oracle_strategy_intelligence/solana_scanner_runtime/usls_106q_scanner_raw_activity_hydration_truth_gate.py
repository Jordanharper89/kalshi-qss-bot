from __future__ import annotations
import asyncio,inspect,json,time
from pathlib import Path

RAW="runtime_state/solana_opportunities/solana_scanner/raw_program_activity.jsonl"

def _walk(obj,key):
 if isinstance(obj,dict):
  if obj.get(key) not in (None,""): return obj.get(key)
  for v in obj.values():
   x=_walk(v,key)
   if x not in (None,""): return x
 elif isinstance(obj,list):
  for v in obj:
   x=_walk(v,key)
   if x not in (None,""): return x
 return None

def _sig(n):
 for k in ("signature","sig"):
  x=_walk(n,k)
  if x: return str(x)
 return None

def _slot(n):
 x=_walk(n,"slot")
 try:return int(x) if x is not None else None
 except Exception:return None

def _family(n):
 for k in ("family","venue","launcher_family","source_family"):
  x=_walk(n,k)
  if x:return str(x)
 return None

def load_raw(root):
 p=Path(root)/RAW;rows=[]
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip(): rows.append(json.loads(line))
 return rows

async def _call(fn,*args,**kwargs):
 v=fn(*args,**kwargs)
 return await v if inspect.isawaitable(v) else v

async def hydrate(root,max_samples=30):
 from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_083_persistent_event_driven_runtime import _hydrate
 raw=load_raw(root)
 uniq=[];seen=set()
 for r in reversed(raw):
  n=r.get("raw_notification") or {}
  s=r.get("signature") or _sig(n)
  if not s or s in seen:continue
  seen.add(s);uniq.append((r,n,s,_slot(n),_family(n)))
  if len(uniq)>=max_samples:break
 out=[]
 for r,n,s,slot,fam in uniq:
  started=time.time();err=None;h=None
  try:h=await _call(_hydrate,s,slot,time.time())
  except Exception as e:err=repr(e)
  out.append({"signature":s,"slot":slot,"family_hint":fam,"error":err,
   "elapsed_seconds":time.time()-started,"hydrated":h})
 return raw,out

def _shape(x):
 if not isinstance(x,dict):return {"type":type(x).__name__}
 return {"keys":sorted(x.keys())[:120],
  "list_shapes":[{"key":k,"len":len(v)} for k,v in x.items() if isinstance(v,list)]}

def run(root,max_samples=30):
 raw,hydrated=asyncio.run(hydrate(root,max_samples))
 ok=[x for x in hydrated if x["error"] is None and isinstance(x["hydrated"],dict)]
 fam={}
 for r in raw:
  f=_family(r.get("raw_notification") or {}) or "UNKNOWN"
  fam[f]=fam.get(f,0)+1
 return {"revision":"USLS_106Q","raw_record_count":len(raw),
  "sampled_signatures":len(hydrated),"hydrated_ok":len(ok),
  "hydration_errors":len(hydrated)-len(ok),"family_counts":fam,
  "samples":[{"signature":x["signature"],"slot":x["slot"],"family_hint":x["family_hint"],
   "error":x["error"],"hydrated_shape":_shape(x["hydrated"])} for x in hydrated],
  "hydrated_rows":[x["hydrated"] for x in ok],
  "finding":"RAW_PROGRAM_ACTIVITY_CAN_BE_HYDRATED_BEFORE_BIRTH_CLASSIFICATION" if ok else "RAW_HYDRATION_NOT_PROVEN",
  "next_boundary":"EXACT_BIRTH_DECODING_FROM_HYDRATED_RAW_ACTIVITY",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root,max_samples=30):
 d=run(root,max_samples)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_raw_activity_hydration_truth_gate.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
