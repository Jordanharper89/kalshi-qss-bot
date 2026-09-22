from __future__ import annotations
import json,time
from dataclasses import dataclass,asdict,is_dataclass
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
from qseries_v2.oracle_adapters.independent.oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes

DBC="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"

@dataclass(frozen=True,slots=True)
class B:
 head_slot:int
 blocks:tuple

def _birth(e):
 low="\n".join(str(x).lower() for x in (getattr(e,"log_messages",()) or ()))
 return ("program log: create pool" in low and
         "instruction: initializepoolwithdynamicconfig" in low and
         DBC.lower() in low and DAMM.lower() in low)

def _dump(e):
 return asdict(e) if is_dataclass(e) else {n:getattr(e,n) for n in dir(e) if not n.startswith("_") and not callable(getattr(e,n))}

def cycle(root):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 sp=base/"incremental_confirmed_head_state.json";ip=base/"incremental_confirmed_birth_inbox.json"
 st=json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
 t0=time.time();head=int(_rpc("getSlot",[{"commitment":"confirmed"}],15.0))
 last=st.get("last_slot");slot=head if last is None else min(head,max(int(last)+1,head-1))
 block=_rpc("getBlock",[slot,{"commitment":"confirmed","encoding":"jsonParsed","transactionDetails":"full","rewards":False,"maxSupportedTransactionVersion":1}],20.0)
 fetched=time.time()
 envs=canonical_transaction_envelopes(B(head,((slot,block),) if block else ()))
 old=json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {"births":[]};births=list(old.get("births") or [])
 seen={x.get("signature") for x in births};new=[]
 for e in envs:
  if not getattr(e,"success",False) or not _birth(e):continue
  sig=str(getattr(e,"signature",""))
  if sig in seen:continue
  bt=getattr(e,"block_time",None);obs=time.time()
  row={"signature":sig,"slot":int(getattr(e,"slot",0)),"block_time":bt,"observed_unix":obs,
       "age_seconds":None if bt is None else max(0.0,obs-float(bt)),
       "envelope":_dump(e),"state":"CONFIRMED_BIRTH_CAPTURED","execution_authority":False}
  births.append(row);new.append(row);seen.add(sig)
 done=time.time()
 st={"revision":"SULS_057","last_slot":slot,"head_slot":head,"last_cycle_unix":done,
     "rpc_seconds":fetched-t0,"cycle_seconds":done-t0,"execution_authority":False}
 ipout={"revision":"SULS_057","birth_count":len(births),"births":births,"execution_authority":False,"read_only":True}
 sp.write_text(json.dumps(st,indent=2,sort_keys=True),encoding="utf-8")
 ip.write_text(json.dumps(ipout,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return {"slot":slot,"head_slot":head,"transactions":len(envs),"new_births":len(new),
         "total_births":len(births),"rpc_seconds":fetched-t0,"cycle_seconds":done-t0}

