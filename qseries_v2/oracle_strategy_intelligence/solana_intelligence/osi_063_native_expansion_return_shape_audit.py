from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
    select_live_solana_token,
    expand_live_solana_token_pools,
)

def _shape(v,depth=0):
 if depth>3:
  return {"type":type(v).__name__}
 if isinstance(v,dict):
  return {
   "type":"dict",
   "keys":sorted(str(k) for k in v.keys()),
   "children":{str(k):_shape(x,depth+1) for k,x in list(v.items())[:20]},
  }
 if isinstance(v,(list,tuple)):
  return {
   "type":type(v).__name__,
   "length":len(v),
   "items":[_shape(x,depth+1) for x in list(v)[:5]],
  }
 attrs={}
 for name in dir(v):
  if name.startswith("_"):
   continue
  try:
   x=getattr(v,name)
  except Exception:
   continue
  if callable(x):
   continue
  attrs[name]=_shape(x,depth+1)
  if len(attrs)>=30:
   break
 return {"type":type(v).__name__,"attributes":attrs}

def audit(root):
 asset=str(select_live_solana_token(timeout_seconds=20.0))
 if not asset:
  raise RuntimeError("NO_CURRENT_LIVE_SOLANA_TOKEN")
 raw=expand_live_solana_token_pools(token_address=asset,timeout_seconds=20.0)
 return {
  "revision":"OSI_063D",
  "asset_key":asset,
  "return_type":type(raw).__name__,
  "shape":_shape(raw),
  "execution_authority":False,
  "read_only":True,
 }

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/native_expansion_return_shape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
