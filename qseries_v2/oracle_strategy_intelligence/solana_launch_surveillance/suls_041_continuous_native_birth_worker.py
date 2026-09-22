from __future__ import annotations
import json,time
from pathlib import Path
from dataclasses import asdict,is_dataclass
from qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
from qseries_v2.oracle_adapters.independent.oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes

DBC="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"

def _birth(e):
 logs=list(getattr(e,"log_messages",()) or ())
 low="\n".join(str(x).lower() for x in logs)
 return (
  "program log: create pool" in low and
  "instruction: initializepoolwithdynamicconfig" in low and
  DBC in low and DAMM in low
 )

def _jsonable(e):
 if is_dataclass(e): return asdict(e)
 return {n:getattr(e,n) for n in dir(e) if not n.startswith("_") and not callable(getattr(e,n))}

def cycle(root,limit=4):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 statep=base/"continuous_native_birth_worker_state.json"
 inboxp=base/"continuous_native_birth_inbox.json"
 state=json.loads(statep.read_text(encoding="utf-8")) if statep.exists() else {}
 start=state.get("next_slot")
 batch=acquire_finalized_block_batch(start_slot=start,limit=limit)
 envs=canonical_transaction_envelopes(batch)
 old=json.loads(inboxp.read_text(encoding="utf-8")) if inboxp.exists() else {"births":[]}
 births=list(old.get("births") or [])
 seen={x.get("signature") for x in births}
 new=[]
 for e in envs:
  if not getattr(e,"success",False) or not _birth(e): continue
  sig=str(getattr(e,"signature",""))
  if sig in seen: continue
  row={"signature":sig,"slot":int(getattr(e,"slot",0)),
   "block_time":getattr(e,"block_time",None),"observed_unix":time.time(),
   "envelope":_jsonable(e),"state":"NATIVE_BIRTH_CAPTURED","execution_authority":False}
  births.append(row);new.append(row);seen.add(sig)
 slots=tuple(getattr(batch,"finalized_slots",()) or ())
 next_slot=(max(slots)+1) if slots else start
 state={"revision":"SULS_041","next_slot":next_slot,"last_head_slot":getattr(batch,"head_slot",None),
  "last_cycle_unix":time.time(),"execution_authority":False}
 inbox={"revision":"SULS_041","birth_count":len(births),"births":births,
  "execution_authority":False,"read_only":True}
 statep.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 inboxp.write_text(json.dumps(inbox,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return {"blocks":len(getattr(batch,"blocks",()) or ()),"transactions":len(envs),
  "new_births":len(new),"total_births":len(births),"next_slot":next_slot}

