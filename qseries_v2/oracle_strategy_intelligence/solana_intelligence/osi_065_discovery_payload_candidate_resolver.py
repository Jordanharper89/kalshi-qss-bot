from __future__ import annotations
import json,re
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import (
    discover_live_solana_tokens,
    expand_live_solana_token_pools,
)

BASE58_RE=re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,48}$")

def _token_entry_shape(v):
 if isinstance(v,dict):
  return {"type":"dict","keys":sorted(str(k) for k in v.keys())}
 if isinstance(v,(list,tuple)):
  return {"type":type(v).__name__,"length":len(v),"items":[_token_entry_shape(x) for x in list(v)[:5]]}
 if isinstance(v,str):
  return {"type":"str","value":v}
 attrs={}
 for k in ("token_address","address","mint","base_address","subject","symbol","name"):
  try:x=getattr(v,k)
  except Exception:x=None
  if x is not None:attrs[k]=x
 return {"type":type(v).__name__,"attributes":attrs}

def _extract_token(v):
 if isinstance(v,str):
  return v if BASE58_RE.match(v) else None
 if isinstance(v,dict):
  for k in ("token_address","address","mint","base_address"):
   x=v.get(k)
   if isinstance(x,str) and BASE58_RE.match(x):return x
  return None
 for k in ("token_address","address","mint","base_address"):
  try:x=getattr(v,k)
  except Exception:x=None
  if isinstance(x,str) and BASE58_RE.match(x):return x
 return None

def _usable_pools(raw):
 payload=getattr(raw,"payload",{}) or {}
 pools=payload.get("pools") or ()
 out=[]
 for p in pools:
  if not isinstance(p,dict):continue
  if not p.get("pair_address") or p.get("price_usd") in (None,""):continue
  out.append({
   "pair_address":str(p["pair_address"]),
   "price_usd":str(p["price_usd"]),
   "liquidity_usd":p.get("liquidity_usd"),
   "volume_h24":p.get("volume_h24"),
   "pair_created_at":p.get("pair_created_at"),
   "dex_id":p.get("dex_id"),
  })
 return out

def audit(root):
 raw=discover_live_solana_tokens(timeout_seconds=20.0)
 payload=getattr(raw,"payload",{}) or {}
 tokens=payload.get("tokens") or ()
 shapes=[_token_entry_shape(x) for x in list(tokens)[:10]]

 candidates=[]
 for item in tokens:
  t=_extract_token(item)
  if t and t not in candidates:candidates.append(t)

 results=[]
 for token in candidates[:30]:
  try:
   expanded=expand_live_solana_token_pools(token_address=token,timeout_seconds=20.0)
   pools=_usable_pools(expanded)
   results.append({
    "token_address":token,
    "usable_pool_count":len(pools),
    "usable_pools":pools,
    "return_type":type(expanded).__name__,
    "ok":True,
   })
  except Exception as e:
   results.append({
    "token_address":token,
    "usable_pool_count":0,
    "usable_pools":[],
    "ok":False,
    "error":f"{type(e).__name__}: {e}",
   })

 viable=[x for x in results if x["usable_pool_count"]>0]
 return {
  "revision":"OSI_065E",
  "discovery_return_type":type(raw).__name__,
  "declared_token_count":payload.get("token_count"),
  "tokens_container_type":type(tokens).__name__,
  "token_entry_shapes":shapes,
  "candidate_count":len(candidates),
  "candidates":candidates,
  "results":results,
  "viable_count":len(viable),
  "first_viable":None if not viable else viable[0],
  "execution_authority":False,
  "read_only":True,
 }

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/live_token_candidate_viability.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
