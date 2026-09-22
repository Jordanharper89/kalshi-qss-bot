from __future__ import annotations
import json,time
from dataclasses import asdict,is_dataclass,dataclass
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_052_confirmed_native_block_capture import acquire_confirmed_block_batch
from qseries_v2.oracle_adapters.independent.oad_319_solana_transaction_canonical_envelope import canonical_transaction_envelopes

DBC="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"

@dataclass(frozen=True,slots=True)
class BridgeBatch:
 head_slot:int
 blocks:tuple

def _is_birth(e):
 logs=list(getattr(e,"log_messages",()) or ())
 low="\n".join(str(x).lower() for x in logs)
 return ("program log: create pool" in low and
  "instruction: initializepoolwithdynamicconfig" in low and
  DBC.lower() in low and DAMM.lower() in low)

def _dump(e):
 if is_dataclass(e):return asdict(e)
 return {n:getattr(e,n) for n in dir(e) if not n.startswith("_") and not callable(getattr(e,n))}

def run(limit=8):
 b=acquire_confirmed_block_batch(limit)
 envs=canonical_transaction_envelopes(BridgeBatch(b.head_slot,b.blocks));now=time.time();births=[]
 for e in envs:
  if getattr(e,"success",False) and _is_birth(e):
   bt=getattr(e,"block_time",None)
   births.append({"signature":str(getattr(e,"signature","")),"slot":int(getattr(e,"slot",0)),
    "block_time":bt,"observed_unix":now,"age_seconds":None if bt is None else max(0.0,now-float(bt)),
    "envelope":_dump(e),"trigger_commitment":"confirmed","state":"CONFIRMED_BIRTH_TRIGGERED",
    "execution_authority":False})
 return {"revision":"SULS_054","transactions_examined":len(envs),"birth_count":len(births),
  "births":births,"execution_authority":False,"read_only":True}

def write(root):
 d=run();p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_meteora_birth_detector.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
