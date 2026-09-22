from __future__ import annotations
import json,time
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc

@dataclass(frozen=True,slots=True)
class ConfirmedBlockBatch:
 head_slot:int
 blocks:tuple
 commitment:str="confirmed"
 execution_authority:bool=False

def acquire_confirmed_block_batch(limit=2):
 head=int(_rpc("getSlot",[{"commitment":"confirmed"}],15.0))
 start=max(0,head-max(1,int(limit))+1);rows=[]
 for slot in range(start,head+1):
  try:
   b=_rpc("getBlock",[slot,{"commitment":"confirmed","encoding":"jsonParsed",
      "transactionDetails":"full","rewards":False,"maxSupportedTransactionVersion":1}],20.0)
   if b:rows.append((slot,b))
  except Exception:continue
 return ConfirmedBlockBatch(head,tuple(rows))

def write(root):
 b=acquire_confirmed_block_batch(2);now=time.time()
 ages=[max(0.0,now-float(x[1].get("blockTime"))) for x in b.blocks if x[1].get("blockTime") is not None]
 d={"revision":"SULS_052","head_slot":b.head_slot,"block_count":len(b.blocks),
  "min_age_seconds":min(ages) if ages else None,"max_age_seconds":max(ages) if ages else None,
  "confirmed_capture_ready":bool(b.blocks),"execution_authority":False,"read_only":True}
 p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_native_block_capture.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
