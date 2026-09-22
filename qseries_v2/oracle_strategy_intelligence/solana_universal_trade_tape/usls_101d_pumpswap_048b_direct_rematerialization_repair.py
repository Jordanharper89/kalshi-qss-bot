from __future__ import annotations
import importlib,json
from pathlib import Path

MODNAME="qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_048b_shared_universal_economic_normalizer"

def rematerialize(root):
 m=importlib.import_module(MODNAME)
 if hasattr(m,"write"):
  r=m.write(root)
  d=r[1] if isinstance(r,tuple) and len(r)>=2 else r
 elif hasattr(m,"build"):
  d=m.build(root)
 else:
  raise RuntimeError("USLS_048B_HAS_NO_BUILD_OR_WRITE")
 if not isinstance(d,dict):
  raise RuntimeError("USLS_048B_DID_NOT_RETURN_DICT")
 return d

def exact_rows(d):
 target=int(d.get("exact_trade_count") or 0)
 candidates=[]
 for k,v in d.items():
  if isinstance(v,list) and v and all(isinstance(x,dict) for x in v):
   score=sum(x.get("venue")=="PUMP_SWAP" for x in v)
   candidates.append((k,v,score))
 if target:
  exact=[z for z in candidates if len(z[1])==target]
  if exact:
   exact.sort(key=lambda z:z[2],reverse=True)
   return exact[0][0],exact[0][1]
 candidates.sort(key=lambda z:(z[2],len(z[1])),reverse=True)
 if candidates:return candidates[0][0],candidates[0][1]
 raise RuntimeError("USLS_048B_EXACT_ROW_LIST_NOT_FOUND")

def repair(x):
 y=dict(x)
 old_instruction=y.get("instruction_index")
 old_block=y.get("block_time")
 if old_instruction is not None:
  y["log_index"]=y.get("log_index",old_instruction)
 y["instruction_index"]=None
 y["event_timestamp"]=y.get("event_timestamp",old_block)
 y["block_time"]=None
 sl=dict(y.get("source_lineage") or {})
 sl.update({
  "identity_revision":"USLS_047C",
  "semantic_repair_revision":"USLS_101D",
  "instruction_position_policy":"048B_VALUE_IS_LOG_INDEX_NOT_INSTRUCTION_INDEX",
  "time_policy":"048B_EVENT_TIMESTAMP_RETAINED_AS_EVENT_TIMESTAMP_BLOCK_TIME_UNCLAIMED"
 })
 y["source_lineage"]=sl
 y["execution_authority"]=False
 return y

def build(root):
 src=rematerialize(root)
 key,rows=exact_rows(src)
 repaired=[repair(x) for x in rows]
 return {
  "revision":"USLS_101D",
  "semantic_contract":"PUMPSWAP_048C",
  "source_revision":src.get("revision"),
  "source_exact_list_key":key,
  "exact_trade_count":len(repaired),
  "source_pending_raw_count":src.get("pending_raw_count"),
  "rows":repaired,
  "repairs":{
   "instruction_index_semantics":True,
   "event_vs_block_time_separation":True,
   "identity_revision_047c":True,
   "direct_048b_rematerialization":True
  },
  "profitability_claimed":False,
  "execution_authority":False,
  "read_only":True
 }

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
