from __future__ import annotations
import json,inspect
from pathlib import Path
from qseries_v2.oracle_adapters.independent import oad_318_solana_native_finalized_block_stream as src

def probe():
 fn=src.acquire_finalized_block_batch
 sig=inspect.signature(fn)
 kwargs={}
 for name,p in sig.parameters.items():
  if p.default is not inspect._empty:continue
  if "count" in name or "limit" in name or "batch" in name:kwargs[name]=1
  elif "timeout" in name:kwargs[name]=20.0
 try:
  raw=fn(**kwargs)
  err=None
 except Exception as e:
  return {"revision":"SULS_012","signature":str(sig),"kwargs":kwargs,"ok":False,
   "error":f"{type(e).__name__}: {e}","execution_authority":False}
 typ=type(raw).__name__
 shape={"type":typ}
 if isinstance(raw,dict):shape["keys"]=sorted(raw.keys())
 elif isinstance(raw,(list,tuple)):
  shape["length"]=len(raw)
  if raw:
   x=raw[0];shape["first_type"]=type(x).__name__
   if isinstance(x,dict):shape["first_keys"]=sorted(x.keys())
   elif hasattr(x,"__dict__"):shape["first_attrs"]=sorted(k for k in vars(x) if not k.startswith("_"))
 elif hasattr(raw,"__dict__"):shape["attrs"]=sorted(k for k in vars(raw) if not k.startswith("_"))
 return {"revision":"SULS_012","signature":str(sig),"kwargs":kwargs,"ok":True,"shape":shape,
  "execution_authority":False}

def write(root):
 d=probe();p=root/"runtime_state/solana_opportunities/launch_surveillance/native_block_shape_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
