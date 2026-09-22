from __future__ import annotations
import json,time
from qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch

def probe():
 now=time.time();b=acquire_finalized_block_batch(limit=1)
 blocks=list(getattr(b,"blocks",()) or ())
 if not blocks:return {"revision":"SULS_046","ok":False,"error":"NO_FINALIZED_BLOCK","execution_authority":False}
 slot,blk=blocks[-1];bt=blk.get("blockTime")
 age=None if bt is None else max(0.0,now-float(bt))
 return {"revision":"SULS_046","ok":bt is not None,"head_slot":getattr(b,"head_slot",None),
  "sample_slot":slot,"block_time":bt,"observed_unix":now,"finalized_head_age_seconds":age,
  "launch_window_5s_possible":bool(age is not None and age<=5.0),
  "execution_authority":False,"read_only":True}

def write(root):
 d=probe();p=root/"runtime_state/solana_opportunities/launch_surveillance/finalized_head_latency_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
