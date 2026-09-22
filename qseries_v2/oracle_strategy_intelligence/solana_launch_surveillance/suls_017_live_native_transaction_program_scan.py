from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from qseries_v2.oracle_adapters.independent.oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes

def _program_ids(env):
 out=set()
 raw=getattr(env,"raw",None)
 if raw is None:
  raw=getattr(env,"raw_transaction",None)
 if isinstance(raw,dict):
  tx=raw.get("transaction") or {};msg=tx.get("message") or {}
  keys=msg.get("accountKeys") or ()
  resolved=[]
  for k in keys:
   if isinstance(k,str):resolved.append(k)
   elif isinstance(k,dict):resolved.append(k.get("pubkey"))
   else:resolved.append(None)
  for ix in msg.get("instructions") or ():
   if isinstance(ix,dict):
    if ix.get("programId"):out.add(str(ix["programId"]))
    pi=ix.get("programIdIndex")
    if isinstance(pi,int) and pi<len(resolved) and resolved[pi]:out.add(str(resolved[pi]))
  meta=raw.get("meta") or {}
  for grp in meta.get("innerInstructions") or ():
   for ix in (grp.get("instructions") or ()) if isinstance(grp,dict) else ():
    if isinstance(ix,dict):
     if ix.get("programId"):out.add(str(ix["programId"]))
     pi=ix.get("programIdIndex")
     if isinstance(pi,int) and pi<len(resolved) and resolved[pi]:out.add(str(resolved[pi]))
 return sorted(out)

def scan():
 batch=acquire_finalized_block_batch(limit=4)
 envs=canonical_transaction_envelopes(batch)
 rows=[]
 for e in envs:
  rows.append({"slot":getattr(e,"slot",None),"signature":getattr(e,"signature",None),
   "block_time":getattr(e,"block_time",None),"success":getattr(e,"success",None),
   "program_ids":_program_ids(e),"logs":list(getattr(e,"log_messages",()) or ())[:80]})
 return {"revision":"SULS_017","head_slot":getattr(batch,"head_slot",None),
  "block_count":len(getattr(batch,"blocks",()) or ()),"transaction_count":len(envs),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=scan();p=root/"runtime_state/solana_opportunities/launch_surveillance/live_native_transaction_program_scan.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
